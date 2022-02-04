import requests


BLOCK_STREAM_BASE_URL = 'https://blockstream.info/api'

BLOCK_STREAM_URL_MAP = {
    'block': lambda block_hash: '/block/{}'.format(block_hash),
    'block_hash_by_height': lambda block_height: '/block-height/{}'.format(block_height),
    'block_txs': lambda block_hash, idx: '/block/{}/txs/[:{}]'.format(block_hash, idx),
    'transaction': lambda txid: '/tx/{}'.format(txid),
    'txids': lambda block_hash: '/block/{}/txids'.format(block_hash),
}

BLOCK_HEIGHT_680000 = 680000


class TransactionAncestry(object):
    def __init__(self, block_height):
        self.block_height = block_height
        self.block_hash = self._getBlockHashByHeight()
        self.graph = {}
        self._initializeGraph()

    def _initializeGraph(self):
        txIds = self.getAllTransactionIds()
        for txid in txIds:
            self.graph[txid] = {'count': 0, 'parents': set(), 'visited': False}

    def getLargestAncestryTransactionSets(self, limit):
        self.getAllBlockTransactions()
        self.processTransactionsInGraph()
        print("{} Transactions with the largest ancestry sets: ".format(limit))
        for idx, txid in enumerate(sorted(self.graph, key=lambda tx: self.graph[tx]['count'], reverse=True)):
            if idx == limit:
                break
            print(txid, self.graph[txid]['count'])

    @staticmethod
    def _callApi(method, relativePath, baseUrl=BLOCK_STREAM_BASE_URL):
        response = getattr(requests, method)(
            url=baseUrl + relativePath,
        )
        return response

    def getAllTransactionIds(self):
        response = self._callApi(
            method='get',
            relativePath=BLOCK_STREAM_URL_MAP['txids'](self.block_hash),
        )
        if response.status_code != 200:
            raise Exception('Cannot get the Txids of block: {}!'.format(self.block_hash))

        data = response.json()
        return data

    def getAllBlockTransactions(self):
        txCount = self.getBlockData()['tx_count']
        start, offset = 0, 25
        while start < txCount:
            self.getBlockTransactions(start)
            start += offset

    def getBlockTransactions(self, startIdx=0):
        response = self._callApi(
            method='get',
            relativePath=BLOCK_STREAM_URL_MAP['block_txs'](self.block_hash, startIdx)
        )
        if response.status_code != 200:
            raise Exception('Unable to Get Block Transactions from {}'.format(startIdx))

        data = response.json()
        self.processTransactions(data)

    def processTransactions(self, transactions):
        for transaction in transactions:
            self.processTransaction(transaction)

    def processTransaction(self, transaction):
        txid = transaction['txid']
        for inTx in transaction['vin']:
            inTxid = inTx['txid']
            if inTxid in self.graph:
                self.graph[txid]['parents'].add(inTxid)

    def processTransactionsInGraph(self):
        for txid in self.graph:
            self.processTransactionInGraph(txid)

    def processTransactionInGraph(self, txid):
        if self.graph[txid]['visited']:
            return
        for parent in self.graph[txid]['parents']:
            self.graph[txid]['count'] += 1
            self.processTransactionInGraph(parent)
            self.graph[txid]['count'] += self.graph[parent]['count']
        self.graph[txid]['visited'] = True

    def getBlockData(self):
        response = self._callApi(
            method='get',
            relativePath=BLOCK_STREAM_URL_MAP['block'](self.block_hash)
        )
        if response.status_code != 200:
            raise Exception('No Block found with the given hash!')

        data = response.json()
        return data

    def _getBlockHashByHeight(self):
        response = self._callApi(
            method='get',
            relativePath=BLOCK_STREAM_URL_MAP['block_hash_by_height'](self.block_height)
        )
        if response.status_code != 200:
            raise Exception('No Block found with the given hash!')

        return response.content
