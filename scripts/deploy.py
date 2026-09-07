"""
Contract deployment script for FaceVerificationRegistry.sol on Sepolia / Ethereum testnet.
"""
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.blockchain.contract import CONTRACT_ABI, is_live_configured


def deploy_contract():
    print("==================================================")
    print(" FACE VERIFICATION REGISTRY - CONTRACT DEPLOYMENT")
    print("==================================================")

    if not is_live_configured():
        print("❌ Error: Valid RPC_URL and PRIVATE_KEY are required in .env for contract deployment.")
        print("Please configure your Sepolia RPC and private key.")
        return

    try:
        from web3 import Web3
        from eth_account import Account

        w3 = Web3(Web3.HTTPProvider(settings.RPC_URL))
        account = Account.from_key(settings.PRIVATE_KEY)
        print(f"Deployer Address: {account.address}")
        print(f"Network Chain ID: {settings.CHAIN_ID}")
        print(f"Account Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

        # Compile contract using solcx if available
        try:
            import solcx
            solcx.install_solc("0.8.20")
            contract_file = Path(__file__).resolve().parent.parent / "contracts" / "FaceVerificationRegistry.sol"
            compiled = solcx.compile_files([str(contract_file)], solc_version="0.8.20")
            contract_id = f"{contract_file}:FaceVerificationRegistry"
            bytecode = compiled[contract_id]["bin"]
            abi = compiled[contract_id]["abi"]
        except Exception as e:
            print(f"⚠ Automatic compilation info: {e}. Using precompiled ABI definition.")
            abi = CONTRACT_ABI
            print("Please ensure your contract is compiled or use Remix / Hardhat / Foundry to deploy.")
            return

        ContractFactory = w3.eth.contract(abi=abi, bytecode=bytecode)
        nonce = w3.eth.get_transaction_count(account.address)

        tx = ContractFactory.constructor().build_transaction({
            "chainId": settings.CHAIN_ID,
            "gas": 1500000,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
        })

        signed_tx = account.sign_transaction(tx)
        print("Broadcasting deployment transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction Submitted: {tx_hash.hex()}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✓ Contract Deployed Successfully!")
        print(f"Contract Address: {receipt.contractAddress}")
        print(f"Update your .env file with: CONTRACT_ADDRESS={receipt.contractAddress}")

    except Exception as e:
        print(f"❌ Deployment failed: {e}")


if __name__ == "__main__":
    deploy_contract()
