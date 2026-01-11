package com.concord.federation;

import java.util.UUID;

public class FederationService {
    private ConsensusManager consensusManager;

    public FederationService() {
        this.consensusManager = new ConsensusManager();
        System.out.println("CONCORD Federation Service Initialized");
    }

    public void syncNarrative(String narrativeId) {
        UUID id = UUID.fromString(narrativeId);

        // 1. Acquire Lock
        if (consensusManager.acquireLock(id, "node-primary")) {
            System.out.println("Lock acquired for narrative: " + narrativeId);

            // 2. Propose Fact (Simulate 3 votes)
            consensusManager.proposeFact(id.toString());
            consensusManager.proposeFact(id.toString());
            boolean committed = consensusManager.proposeFact(id.toString()); // 3rd vote hits quorum

            if (committed) {
                System.out.println("✅ Fact COMMITTED to Ledger via Consensus.");
            } else {
                System.out.println("❌ Fact REJECTED. Insufficient votes.");
            }

            consensusManager.releaseLock(id);
            System.out.println("Sync complete.");
        } else {
            System.out.println("Narrative currently locked by another node.");
        }
    }

    public static void main(String[] args) {
        FederationService service = new FederationService();
        service.syncNarrative(UUID.randomUUID().toString());

        // Keep container alive
        try {
            while (true) {
                Thread.sleep(10000);
            }
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
