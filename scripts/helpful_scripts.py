from brownie import network, config, accounts


def get_account():
    if network.show_active() in ["development"]:
        return accounts[0]
    elif network.show_active() == "ganache-local":
        print(f"Using the account testing saved locally")
        return accounts.load("testing")
    else:
        return accounts.add(config["wallets"]["from_key"])
