# Sequential DA failure measurements

Accepted windows: T13a, T13b, T13r, T14a, T14b, T14r.

T13 uses a normal pool and T14 uses an HA pool. Each mode measures the first DA failure, the second DA failure after verified seg2 operation, and both DAs returning. The first DA stays off until the second fault and seg3 recovery are complete. Both IKE pairs are preserved across all three windows of each mode.

Window logs retain original lines through the after-action snapshot; packet traces are complete. Per-node and core evidence records routes, domains, MCS, tunnel groups and operational BFD intervals. Pool preparation is outside measured windows. The baseline BFD capture is read-only after final restoration. `source-metadata.json` identifies the invocation and runner checksum.
