from brownie import Voting, accounts, exceptions, web3
import pytest


def teststartVotingPeriod():

    # Arrange
    account = accounts[0]
    voting = Voting.deploy({"from": account})

    # Test that only the owner can call this function
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.startVotingPeriod(1, {"from": accounts[1]})
        transaction.wait(1)

    # Test that the state changes to Open (0)
    transaction = voting.startVotingPeriod(1, {"from": account})
    transaction.wait(1)
    expected = 0
    assert voting.voting_state() == expected

    # Test that the voting cannot be opened if already open
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.startVotingPeriod(1, {"from": account})
        transaction.wait(1)


def testrunAsCandidate():

    print("I'm starting testrunAsCandidate")
    # Arrange
    account = accounts[0]
    voting = Voting.deploy({"from": account})
    candidate_name = "Michel"

    # Test that the voting period is open
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.runAsCandidate(candidate_name, {"from": account})
        transaction.wait(1)

    # Arrange
    transaction = voting.startVotingPeriod(1, {"from": account})
    transaction.wait(1)
    transaction = voting.runAsCandidate(candidate_name, {"from": account})
    transaction.wait(1)

    # Test that the Candidate has been added
    (isCandidate, fundAmount, numberOfVotes, name) = voting.candidateToProfile(account)
    assert isCandidate
    assert fundAmount == 0
    assert numberOfVotes == 0
    assert name == "Michel"

    # Test that the user cannot run for candidate again
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.runAsCandidate(candidate_name, {"from": account})
        transaction.wait(1)


def testvote():

    # Arrange
    account = accounts[0]
    voting = Voting.deploy({"from": account})

    # Test that the voting period is open
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.vote(accounts[1], {"from": account})
        transaction.wait(1)

    # Arrange
    transaction = voting.startVotingPeriod(1, {"from": account})
    transaction.wait(1)

    # Test that we can only vote for someone running as a candidate
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.vote(accounts[1], {"from": account})
        transaction.wait(1)

    # Arrange
    transaction = voting.runAsCandidate("Michel", {"from": accounts[1]})
    transaction.wait(1)
    transaction = voting.vote(accounts[1], {"from": account})
    transaction.wait(1)
    (isCandidate, fundAmount, numberOfVotes, name) = voting.candidateToProfile(
        accounts[1]
    )
    assert voting.voterToCandidate(account) == accounts[1]
    assert isCandidate
    assert fundAmount == 0
    assert numberOfVotes == 1
    assert name == "Michel"

    # Test that one voter cannot vote twice
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.vote(accounts[1], {"from": account})
        transaction.wait(1)


def testfund():

    # Arrange
    voter = accounts[0]
    candidate = accounts[1]
    goodfunding_amount = web3.toWei("0.05", "ether")
    badfunding_amount = web3.toWei("0.001", "ether")
    voting = Voting.deploy({"from": voter})
    minimum_number_of_votes = 5

    # Test that the voting period is open
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.fund(
            candidate, {"from": voter, "value": goodfunding_amount}
        )
        transaction.wait(1)

    # Arrange
    transaction = voting.startVotingPeriod(minimum_number_of_votes, {"from": voter})
    transaction.wait(1)

    # Test that we can only vote for someone running as a candidate
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.fund(
            candidate, {"from": voter, "value": goodfunding_amount}
        )
        transaction.wait(1)

    # Arrange
    transaction = voting.runAsCandidate("Michel", {"from": candidate})
    transaction.wait(1)

    # Test that the minimum amount is 0.01
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.fund(
            candidate, {"from": voter, "value": badfunding_amount}
        )
        transaction.wait(1)

    # Test that the candidate has at least 5 votes before receiving funding
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.fund(
            candidate, {"from": voter, "value": goodfunding_amount}
        )
        transaction.wait(1)

    # Arrange
    transaction = voting.vote(candidate, {"from": accounts[2]})
    transaction.wait(1)
    transaction = voting.vote(candidate, {"from": accounts[3]})
    transaction.wait(1)
    transaction = voting.vote(candidate, {"from": accounts[4]})
    transaction.wait(1)
    transaction = voting.vote(candidate, {"from": accounts[5]})
    transaction.wait(1)
    transaction = voting.vote(candidate, {"from": accounts[6]})
    transaction.wait(1)

    # Test that the funder has voted for the candidate being funded
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.delegate(
            candidate, {"from": voter, "value": goodfunding_amount}
        )
        transaction.wait(1)

    # Arrange
    transaction = voting.vote(candidate, {"from": voter})
    transaction.wait(1)
    transaction = voting.fund(candidate, {"from": voter, "value": goodfunding_amount})
    transaction.wait(1)

    # Assert
    (isCandidate, fundAmount, numberOfVotes, name) = voting.candidateToProfile(
        candidate
    )
    assert voting.voterToCandidate(voter) == candidate
    assert isCandidate
    assert fundAmount == goodfunding_amount
    assert numberOfVotes == 6
    assert goodfunding_amount == voting.voterToAmountFunded(voter)
    assert name == "Michel"


def testdelegate():

    # Arrange
    delegater = accounts[0]
    delegatee = accounts[1]
    funding_amount = web3.toWei("0.7", "ether")

    voting = Voting.deploy({"from": delegater})

    # Test that the voting period is open
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.delegate(delegatee, {"from": delegater})
        transaction.wait(1)

    # Arrange
    transaction = voting.startVotingPeriod(1, {"from": delegater})
    transaction.wait(1)

    # Test that a user can only delegate if he's a candidate
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.delegate(delegatee, {"from": delegater})
        transaction.wait(1)

    # Arrange
    transaction = voting.runAsCandidate("Michel", {"from": delegater})
    transaction.wait(1)

    # Test that we can only delegate for someone running as a candidate
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.delegate(delegatee, {"from": delegater})
        transaction.wait(1)

    # Arrange
    transaction = voting.runAsCandidate("Robert", {"from": delegatee})
    transaction.wait(1)

    # Test that the delegatee has at least 5 votes
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.delegate(delegatee, {"from": delegater})
        transaction.wait(1)

    # Arrange - ensure the delegatee has 5 votes
    transaction = voting.vote(delegatee, {"from": delegatee})
    transaction.wait(1)
    transaction = voting.vote(delegatee, {"from": accounts[2]})
    transaction.wait(1)
    transaction = voting.vote(delegatee, {"from": accounts[3]})
    transaction.wait(1)
    transaction = voting.vote(delegatee, {"from": accounts[4]})
    transaction.wait(1)
    transaction = voting.vote(delegatee, {"from": accounts[5]})
    transaction.wait(1)

    # we also want the delegater to have some funds so he needs 5 votes
    transaction = voting.vote(delegater, {"from": delegater})
    transaction.wait(1)
    transaction = voting.vote(delegater, {"from": accounts[6]})
    transaction.wait(1)
    transaction = voting.vote(delegater, {"from": accounts[7]})
    transaction.wait(1)
    transaction = voting.vote(delegater, {"from": accounts[8]})
    transaction.wait(1)
    transaction = voting.vote(delegater, {"from": accounts[9]})
    transaction.wait(1)
    # Then we fund the delegater
    transaction = voting.fund(delegater, {"from": accounts[6], "value": funding_amount})
    transaction.wait(1)
    # and the delegater delegates to the delegatee
    transaction = voting.delegate(delegatee, {"from": delegater})
    transaction.wait(1)

    # Assert
    (
        isCandidateDelegatee,
        fundAmountDelegatee,
        numberOfVotesDelegatee,
        name,
    ) = voting.candidateToProfile(delegatee)
    assert isCandidateDelegatee
    assert fundAmountDelegatee == 0
    assert numberOfVotesDelegatee == 10
    assert name == "Robert"

    (
        isCandidateDelegater,
        fundAmountDelegater,
        numberOfVotesDelegater,
        name,
    ) = voting.candidateToProfile(delegater)
    assert isCandidateDelegater == False
    assert fundAmountDelegater == funding_amount
    assert numberOfVotesDelegater == 0
    assert name == "Michel"


def test_electCandidate():

    # Arrange
    owner = accounts[0]
    candidate = accounts[1]
    candidate2 = accounts[2]
    candidate3 = accounts[3]

    voting = Voting.deploy({"from": owner})

    # Test that the voting period is open
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.electCandidate({"from": owner})
        transaction.wait(1)

    # Arrange
    transaction = voting.startVotingPeriod(1, {"from": owner})
    transaction.wait(1)

    # Test that a user can only delegate if he's the owner
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.electCandidate({"from": candidate})
        transaction.wait(1)

    # Test that the owner can only elect if a candidate is running
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.electCandidate({"from": owner})
        transaction.wait(1)

    # Arrange
    transaction = voting.runAsCandidate("Michel", {"from": candidate})
    transaction.wait(1)
    transaction = voting.vote(candidate, {"from": candidate})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Robert", {"from": candidate2})
    transaction.wait(1)
    transaction = voting.vote(candidate2, {"from": candidate2})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Dave", {"from": candidate3})
    transaction.wait(1)
    transaction = voting.vote(candidate3, {"from": candidate3})
    transaction.wait(1)
    transaction = voting.vote(candidate3, {"from": owner})
    transaction.wait(1)
    transaction = voting.electCandidate({"from": owner})
    transaction.wait(1)

    assert voting.electedCandidate() == candidate3

    # Test that we cannot re-run the election
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.electCandidate({"from": owner})
        transaction.wait(1)


def test_electCandidate_with_funding():

    # Arrange
    owner = accounts[0]
    candidate = accounts[1]
    candidate2 = accounts[2]
    candidate3 = accounts[3]
    funding_amount = web3.toWei("0.7", "ether")

    # Deploy
    voting = Voting.deploy({"from": owner})

    # Start voting period
    transaction = voting.startVotingPeriod(1, {"from": owner})
    transaction.wait(1)

    # Candidates running, voting and funding
    transaction = voting.runAsCandidate("Michel", {"from": candidate})
    transaction.wait(1)
    transaction = voting.vote(candidate, {"from": candidate})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Robert", {"from": candidate2})
    transaction.wait(1)
    transaction = voting.vote(candidate2, {"from": owner})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Dave", {"from": candidate3})
    transaction.wait(1)
    transaction = voting.vote(candidate3, {"from": candidate3})
    transaction.wait(1)
    transaction = voting.fund(candidate2, {"from": owner, "value": funding_amount})
    transaction.wait(1)
    transaction = voting.electCandidate({"from": owner})
    transaction.wait(1)

    # Assert
    assert voting.electedCandidate() == candidate2


def test_electCandidate_with_history():

    # Arrange
    owner = accounts[0]
    candidate = accounts[1]
    candidate2 = accounts[2]
    candidate3 = accounts[3]

    # Deploy
    voting = Voting.deploy({"from": owner})

    # Start voting period
    transaction = voting.startVotingPeriod(1, {"from": owner})
    transaction.wait(1)

    # Candidates running, voting and funding
    transaction = voting.runAsCandidate("Michel", {"from": candidate})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Robert", {"from": candidate2})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Dave", {"from": candidate3})
    transaction.wait(1)
    transaction = voting.electCandidate({"from": owner})
    transaction.wait(1)

    # Assert
    assert voting.electedCandidate() == candidate


def test_ElectedCandidateFundClaim():

    # Arrange
    owner = accounts[0]
    candidate = accounts[1]
    funding_amount = web3.toWei("0.7", "ether")
    voting = Voting.deploy({"from": owner})
    transaction = voting.startVotingPeriod(1, {"from": owner})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Michel", {"from": candidate})
    transaction.wait(1)

    # Test that the candidate has been elected
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.ElectedCandidateFundClaim({"from": candidate})
        transaction.wait(1)

    # Arrange
    transaction = voting.vote(candidate, {"from": owner})
    transaction.wait(1)
    transaction = voting.fund(candidate, {"from": owner, "amount": funding_amount})
    transaction.wait(1)
    transaction = voting.electCandidate({"from": owner})
    transaction.wait(1)

    # Test that only the elected candidate can claim the funds
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.ElectedCandidateFundClaim({"from": owner})
        transaction.wait(1)

    balance_before = voting.balance()
    print(f"balance before {balance_before}")

    # Arrange
    transaction = voting.ElectedCandidateFundClaim({"from": candidate})
    transaction.wait(1)

    balance_after = voting.balance()
    print(f"balance after {balance_after}")

    # Assert
    assert balance_after == balance_before - funding_amount


def test_voterFundClaim():

    # Arrange
    owner = accounts[0]
    voter = accounts[1]
    voter2 = accounts[4]
    voter3 = accounts[5]
    electedCandidate = accounts[2]
    nonElectedCandidate = accounts[3]
    delegatingCandidate = accounts[6]
    funding_amount_1 = web3.toWei("0.7", "ether")
    funding_amount_2 = web3.toWei("0.3", "ether")
    funding_amount_3 = web3.toWei("0.2", "ether")
    voting = Voting.deploy({"from": owner})
    transaction = voting.startVotingPeriod(1, {"from": owner})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Michel", {"from": electedCandidate})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Robert", {"from": nonElectedCandidate})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Dave", {"from": delegatingCandidate})
    transaction.wait(1)

    # Test that a candidate has been elected
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.voterFundClaim({"from": voter})
        transaction.wait(1)

    # Voting and funding electedCandidate
    transaction = voting.vote(electedCandidate, {"from": owner})
    transaction.wait(1)
    transaction = voting.vote(electedCandidate, {"from": voter})
    transaction.wait(1)
    transaction = voting.fund(
        electedCandidate, {"from": voter, "amount": funding_amount_1}
    )
    transaction.wait(1)
    # Voting and funding nonElectedCandidate
    transaction = voting.vote(nonElectedCandidate, {"from": voter2})
    transaction.wait(1)
    transaction = voting.fund(
        nonElectedCandidate, {"from": voter2, "amount": funding_amount_2}
    )
    transaction.wait(1)
    # Voting and funding and delegating delegatingCandidate
    transaction = voting.vote(delegatingCandidate, {"from": voter3})
    transaction.wait(1)
    transaction = voting.fund(
        delegatingCandidate, {"from": voter3, "amount": funding_amount_3}
    )
    transaction.wait(1)
    # Delegating
    transaction = voting.delegate(electedCandidate, {"from": delegatingCandidate})
    transaction.wait(1)

    # Election
    transaction = voting.electCandidate({"from": owner})
    transaction.wait(1)

    # Test that the voter for the elected candidate cannot withdraw his funds
    with pytest.raises(exceptions.VirtualMachineError):
        transaction = voting.voterFundClaim({"from": voter})
        transaction.wait(1)

    balance_before = voting.balance()
    print(f"balance before {balance_before}")

    # Voter for the non-elected candidate should be able to claim his funding
    transaction = voting.voterFundClaim({"from": voter2})
    transaction.wait(1)
    # Voter for the delegating candidate should be able to claim his funding
    transaction = voting.voterFundClaim({"from": voter3})
    transaction.wait(1)

    balance_after = voting.balance()
    print(f"balance after {balance_after}")

    # Assert
    assert balance_after == balance_before - funding_amount_2 - funding_amount_3
