import regex as re
from Crypto.Hash import keccak

non_checksummed_patterns = (re.compile(
    "^(0x)?[0-9a-f]{40}$"), re.compile("^(0x)?[0-9A-F]{40}$"))
sol_pattern = re.compile('[0-9a-zA-Z]{44}$')


def validate_eth(addr: str) -> bool:
    """Determines whether a given address is a valid public Ethereum address

    Args:
        addr (str): address that has been entered

    Returns:
        bool: True if the address is valid, false otherwise.
    """
    address = addr
    if any(bool(pat.match(address))
            for pat in non_checksummed_patterns):
        return True
    if not address.startswith('0x'):
        return False
    addr = address[2:]
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(addr.lower().encode('ascii'))
    addr_hash = keccak_hash.hexdigest()
    for i in range(0, len(addr)):
        if any([
                int(addr_hash[i], 16) > 7 and addr[i].upper() != addr[i],
                int(addr_hash[i], 16) <= 7 and addr[i].lower() != addr[i]
        ]):
            return False
    return True


def validate_sol(addr: str) -> bool:
    """Determines whether a given address is a valid public Solana address

    Args:
        addr (str): address that has been entered

    Returns:
        bool: True if the address is valid, false otherwise.
    """
    return sol_pattern.fullmatch(addr)
