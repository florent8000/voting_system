// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";

/*
VOTING SYSTEM
1 - User can run to be a candidate (a user can only run once per voting period)
1 - User can vote for a candidate (only one vote and the candidate needs to isCandidate)
2 - User can vote for a candidate (only one vote per user)
3 - User can fund a candidate if a candidate has at least 5 votes (minimum 0.01 ETH)
4 - Candidate can delegate vote and funding to another candidate (Can only delegate once if has votes already, cannot receive more votes)
5 - Admin can close the voting period and the winner is decided by the number of votes
6 - user who funded non-elected candidates can claim their money back
*/
contract Voting is Ownable {
    address payable public electedCandidate;
    address[] public candidates;
    uint256 public constant MIN_FUNDING_AMOUNT = 0.001 * 10**18;
    uint256 public MIN_NUMBER_OF_VOTES;
    mapping(address => address) public voterToCandidate;
    mapping(address => uint256) public voterToAmountFunded;

    enum VOTING_STATE {
        OPEN,
        CLOSED,
        ELECTING_CANDIDATE,
        CLAIM_PERIOD
    }
    VOTING_STATE public voting_state;

    struct CandidateProfile {
        bool isCandidate;
        uint256 fundedAmount;
        uint256 numberOfVotes;
        string name;
    }
    mapping(address => CandidateProfile) public candidateToProfile;

    event VotingOpened(uint256 min_number_of_votes);
    event NewCandidate(address indexed user, string indexed name);
    event NewVote(address indexed voter, address indexed candidate);
    event Funded(
        address indexed voter,
        address indexed candidate,
        uint256 amountFunded
    );
    event Delegated(
        address indexed delegater,
        address indexed delegatee,
        uint256 numberOfVotes
    );
    event CandidateElected(
        address indexed candidate,
        uint256 amountFunded,
        uint256 numberOfVotes
    );
    event CandidateClaim(address indexed candidate, uint256 amount);
    event VoterClaim(address indexed voter, uint256 amount);

    constructor() {
        voting_state = VOTING_STATE.CLOSED;
    }

    function startVotingPeriod(uint256 _min_number_of_votes) public onlyOwner {
        // The owner can start the voting period if the voting has not already started
        require(
            voting_state == VOTING_STATE.CLOSED,
            "A voting period is already on-going"
        );
        require(_min_number_of_votes >= 0);

        MIN_NUMBER_OF_VOTES = _min_number_of_votes;
        voting_state = VOTING_STATE.OPEN;
        emit VotingOpened(MIN_NUMBER_OF_VOTES);
    }

    function runAsCandidate(string memory _name) public {
        // Voting period needs to be open and the users shouldn't already be a candidate
        require(
            voting_state == VOTING_STATE.OPEN,
            "The voting period has not started"
        );
        require(
            candidateToProfile[msg.sender].isCandidate == false,
            "You are already running as a candidate"
        );
        candidateToProfile[msg.sender] = CandidateProfile(true, 0, 0, _name);
        candidates.push(msg.sender);
        emit NewCandidate(msg.sender, _name);
    }

    function vote(address _candidate) public {
        require(
            voting_state == VOTING_STATE.OPEN,
            "The voting period has not started"
        );
        require(
            voterToCandidate[msg.sender] == address(0),
            "You have already voted"
        );
        require(
            candidateToProfile[_candidate].isCandidate == true,
            "You are voting for someone who is not a candidate"
        );

        voterToCandidate[msg.sender] = _candidate;
        candidateToProfile[_candidate].numberOfVotes += 1;
        emit NewVote(msg.sender, _candidate);
    }

    // User can fund a candidate if a candidate has at least 5 votes (minimum 0.01 ETH)
    function fund(address _candidate) public payable {
        require(
            voting_state == VOTING_STATE.OPEN,
            "The voting period has not started"
        );
        require(
            candidateToProfile[_candidate].isCandidate == true,
            "You are funding for someone who is not a candidate"
        );
        require(
            candidateToProfile[_candidate].numberOfVotes >= MIN_NUMBER_OF_VOTES,
            "The candidate needs at a minimum number of votes to receive funding"
        );
        require(
            msg.value >= MIN_FUNDING_AMOUNT,
            "Your funding amount is below the minimum 0.01 ETH"
        );
        require(
            voterToCandidate[msg.sender] == _candidate,
            "You are funding a candidate you didn't vote for"
        );

        voterToAmountFunded[msg.sender] += msg.value;
        candidateToProfile[_candidate].fundedAmount += msg.value;
        emit Funded(msg.sender, _candidate, msg.value);
    }

    modifier onlyCandidate() {
        require(
            candidateToProfile[msg.sender].isCandidate == true,
            "You are not a candidate"
        );
        _;
    }

    // 4 - Candidate can delegate vote to another candidate (Can only delegate once if has votes already, cannot receive more votes)
    // !! The funding cannot be delegated
    function delegate(address _candidate) public onlyCandidate {
        require(
            voting_state == VOTING_STATE.OPEN,
            "The voting period has not started"
        );
        require(
            candidateToProfile[_candidate].isCandidate == true,
            "You are delegating to someone who is not a candidate"
        );
        require(
            candidateToProfile[_candidate].numberOfVotes >= MIN_NUMBER_OF_VOTES,
            "The delegate candidate needs at least 5 votes to be delegated to"
        );
        require(
            msg.sender != _candidate,
            "you cannot delegate votes to yourself"
        );

        candidateToProfile[_candidate].numberOfVotes += candidateToProfile[
            msg.sender
        ].numberOfVotes;

        // Saving info for the event
        uint256 numberOfVotesTemp = candidateToProfile[msg.sender]
            .numberOfVotes;
        // Re-initializing candidate info
        candidateToProfile[msg.sender].numberOfVotes = 0;
        candidateToProfile[msg.sender].isCandidate = false;

        emit Delegated(msg.sender, _candidate, numberOfVotesTemp);
    }

    // The Candidate with most votes wins. If there's a similar number of votes for multiple candidates,
    // the candidate with the most funding between those candidates wins. If there's similar amount of funding,
    // the candidate who has been running for the longest time wins
    function electCandidate() public onlyOwner {
        // The owner can start the voting period if the voting has not already started
        require(
            voting_state == VOTING_STATE.OPEN,
            "The voting period has not started"
        );
        require(candidates.length > 0, "No Candidate running");
        require(
            electedCandidate == address(0),
            "A candidate has already been elected"
        );

        uint256 maxVotes;
        uint256 maxfunding;
        address winner;

        voting_state = VOTING_STATE.ELECTING_CANDIDATE;

        for (uint256 i = 0; i < candidates.length; i++) {
            if (
                (candidateToProfile[candidates[i]].isCandidate &&
                    candidateToProfile[candidates[i]].numberOfVotes >
                    maxVotes) || winner == address(0)
            ) {
                maxVotes = candidateToProfile[candidates[i]].numberOfVotes;
                maxfunding = candidateToProfile[candidates[i]].fundedAmount;
                winner = candidates[i];
            } else if (
                candidateToProfile[candidates[i]].numberOfVotes == maxVotes &&
                candidateToProfile[candidates[i]].fundedAmount > maxfunding
            ) {
                maxfunding = candidateToProfile[candidates[i]].fundedAmount;
                winner = candidates[i];
            }
        }
        electedCandidate = payable(winner);
        voting_state = VOTING_STATE.CLAIM_PERIOD;
        emit CandidateElected(electedCandidate, maxfunding, maxVotes);
    }

    function ElectedCandidateFundClaim() public payable onlyCandidate {
        // The owner can start the voting period if the voting has not already started
        require(
            voting_state == VOTING_STATE.CLAIM_PERIOD,
            "The election period hasn't started yet"
        );
        require(
            electedCandidate != address(0),
            "No candidate has been elected yet"
        );
        require(
            msg.sender == electedCandidate,
            "You cannot claim funding since you are not the elected candidate"
        );
        // Zero the balance before the transfer to prevent re-entrancy
        uint256 amount = candidateToProfile[electedCandidate].fundedAmount;
        candidateToProfile[electedCandidate].fundedAmount = 0;
        electedCandidate.transfer(amount);
        emit CandidateClaim(electedCandidate, amount);
    }

    // Users who have funded non-elected candidates can claim their funding back
    function voterFundClaim() public payable {
        // The owner can start the voting period if the voting has not already started
        require(
            voting_state == VOTING_STATE.CLAIM_PERIOD,
            "The claiming period isn't open"
        );
        require(
            electedCandidate != address(0),
            "No candidate has been elected yet"
        );
        require(
            voterToCandidate[msg.sender] != electedCandidate,
            "You cannot claim your funds since your candidate has been elected"
        );
        require(
            voterToAmountFunded[msg.sender] > 0,
            "You haven't funded your candidate or you have already claimed your funds"
        );

        // Zero the balance before the transfer to prevent re-entrancy
        uint256 amount = voterToAmountFunded[msg.sender];
        voterToAmountFunded[msg.sender] = 0;
        payable(msg.sender).transfer(amount);
        emit VoterClaim(msg.sender, amount);
    }
}
