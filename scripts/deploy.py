from brownie import Voting, network, config, accounts
from scripts.helpful_scripts import get_account
from web3 import Web3


def deploy():
    account = get_account()
    min_number_of_votes = 1
    # voting = Voting.deploy(
    #     {"from": account},
    #     publish_source=config["networks"][network.show_active()].get("verify"),
    # )
    voting = Voting.deploy({"from": account})
    print(f"Contract deployed to {voting.address}")

    transaction = voting.startVotingPeriod(1, {"from": account})
    transaction.wait(1)
    print(f"The voting has started")


def test():

    voting = Voting[-1]
    account = get_account()

    # Candidates running
    # name = ("Michel").encode("utf-8")  # convert to bytes32
    name = "Michel"
    transaction = voting.runAsCandidate(name, {"from": account})
    transaction.wait(1)
    print(f"{account} ({name}) is running for candidate")

    # Voting
    transaction = voting.vote(account, {"from": account})
    transaction.wait(1)
    print(f"{account} voted for {account}")


def test2():

    voting = Voting[-1]
    account = get_account()
    amount = Web3.toWei("0.003", "ether")

    # Funding
    transaction = voting.fund(account, {"from": account, "amount": amount})
    transaction.wait(1)
    print(f"{account} funded {account} for {account} ether")

    # Election
    transaction = voting.electCandidate({"from": account})
    transaction.wait(1)
    print(f"{voting.electedCandidate()} has been elected!!!")

    return voting


def main():
    # deploy()
    # test()
    test2()
