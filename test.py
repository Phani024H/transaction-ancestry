from transaction_ancestry import TransactionAncestry
from transaction_ancestry import BLOCK_HEIGHT_680000


# Creating a TransactionAncestry object for block height 680000
ta = TransactionAncestry(BLOCK_HEIGHT_680000)
# Print the 10 transactions with largest ancestry sets
ta.getLargestAncestryTransactionSets(limit=10)
