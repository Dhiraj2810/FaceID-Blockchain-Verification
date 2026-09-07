// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FaceVerificationRegistry
 * @dev Stores SHA-256 evidence fingerprints and metadata on-chain for tamper verification.
 */
contract FaceVerificationRegistry {
    struct Record {
        bytes32 contentHash;
        string sourceUrl;
        uint256 timestamp;
    }

    Record[] private records;

    event RecordStored(
        uint256 indexed recordId,
        bytes32 indexed contentHash,
        string sourceUrl,
        uint256 timestamp
    );

    /**
     * @notice Stores a content fingerprint hash and source URL on the blockchain.
     * @param contentHash The 32-byte SHA-256 fingerprint of the evidence file.
     * @param sourceUrl The discovered source web/social URL.
     * @return recordId The unique index of the registered record.
     */
    function storeRecord(bytes32 contentHash, string calldata sourceUrl)
        external
        returns (uint256 recordId)
    {
        recordId = records.length;
        records.push(
            Record({
                contentHash: contentHash,
                sourceUrl: sourceUrl,
                timestamp: block.timestamp
            })
        );

        emit RecordStored(recordId, contentHash, sourceUrl, block.timestamp);
    }

    /**
     * @notice Retrieves a stored evidence record by index.
     * @param recordId Index of the record.
     * @return contentHash The 32-byte SHA-256 fingerprint.
     * @return sourceUrl The discovered source web/social URL.
     * @return timestamp The block timestamp when stored.
     */
    function getRecord(uint256 recordId)
        external
        view
        returns (
            bytes32 contentHash,
            string memory sourceUrl,
            uint256 timestamp
        )
    {
        require(recordId < records.length, "Record index out of bounds.");
        Record memory rec = records[recordId];
        return (rec.contentHash, rec.sourceUrl, rec.timestamp);
    }

    /**
     * @notice Returns total number of registered records.
     */
    function getRecordCount() external view returns (uint256) {
        return records.length;
    }
}
