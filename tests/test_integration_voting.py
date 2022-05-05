from brownie import Voting, accounts, web3


def test_integration():

    # Arrange
    owner = accounts[0]

    voter1 = accounts[1]
    voter2 = accounts[2]
    voter3 = accounts[3]
    voter4 = accounts[4]
    voter5 = accounts[5]
    voter6 = accounts[6]

    minimum_number_of_votes = 2

    electedCandidate = accounts[7]
    nonElectedCandidate1 = accounts[8]
    nonElectedCandidate2 = accounts[9]

    one_ether = web3.toWei("1", "ether")
    five_ether = web3.toWei("5", "ether")

    # Deploy & start voting period
    voting = Voting.deploy({"from": owner})
    transaction = voting.startVotingPeriod(minimum_number_of_votes, {"from": owner})
    transaction.wait(1)

    # Candidates running
    transaction = voting.runAsCandidate("Michel", {"from": electedCandidate})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Robert", {"from": nonElectedCandidate1})
    transaction.wait(1)
    transaction = voting.runAsCandidate("Dave", {"from": nonElectedCandidate2})
    transaction.wait(1)

    # Voting
    transaction = voting.vote(electedCandidate, {"from": voter1})
    transaction.wait(1)
    transaction = voting.vote(electedCandidate, {"from": voter2})
    transaction.wait(1)
    transaction = voting.vote(nonElectedCandidate1, {"from": voter3})
    transaction.wait(1)
    transaction = voting.vote(nonElectedCandidate1, {"from": voter4})
    transaction.wait(1)
    transaction = voting.vote(nonElectedCandidate2, {"from": voter5})
    transaction.wait(1)
    transaction = voting.vote(nonElectedCandidate2, {"from": voter6})
    transaction.wait(1)

    # Funding
    transaction = voting.fund(electedCandidate, {"from": voter1, "amount": one_ether})
    transaction.wait(1)
    transaction = voting.fund(electedCandidate, {"from": voter2, "amount": one_ether})
    transaction.wait(1)
    transaction = voting.fund(
        nonElectedCandidate1, {"from": voter3, "amount": five_ether}
    )
    transaction.wait(1)
    transaction = voting.fund(
        nonElectedCandidate1, {"from": voter4, "amount": five_ether}
    )
    transaction.wait(1)
    transaction = voting.fund(
        nonElectedCandidate2, {"from": voter5, "amount": five_ether}
    )
    transaction.wait(1)
    transaction = voting.fund(
        nonElectedCandidate2, {"from": voter6, "amount": five_ether}
    )
    transaction.wait(1)

    total_balance = one_ether * 2 + five_ether * 4
    assert voting.balance() == total_balance

    # Delegating
    transaction = voting.delegate(electedCandidate, {"from": nonElectedCandidate1})
    transaction.wait(1)

    # Election
    transaction = voting.electCandidate({"from": owner})
    transaction.wait(1)
    assert voting.electedCandidate() == electedCandidate

    # Voter fund claims
    transaction = voting.voterFundClaim({"from": voter3})
    transaction.wait(1)
    assert voting.balance() == total_balance - five_ether
    transaction = voting.voterFundClaim({"from": voter5})
    transaction.wait(1)
    assert voting.balance() == total_balance - five_ether * 2

    # Candidate fund claims
    transaction = voting.ElectedCandidateFundClaim({"from": electedCandidate})
    transaction.wait(1)
    assert voting.balance() == total_balance - five_ether * 2 - one_ether * 2
