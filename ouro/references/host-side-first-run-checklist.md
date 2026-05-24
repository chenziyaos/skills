# Ouro — Host-Side First Run Checklist

> Short execution checklist for the first real host-side governance shadow write.

## Recommended first case
- Use `L5` (inventory-aware `merge-candidate`)

## Checklist

1. **Keep the primary decision intact**  
   Confirm `Decision` is still one of the five routing values.

2. **Surface governance only as advisory**  
   If present, `Governance Signal` must remain candidate/blocking language.

3. **Require a non-null signal before writing**  
   Do not emit a governance artifact when `Governance Signal = null`.

4. **Require a complete evidence envelope**  
   Record all of: `evidence_maturity`, `inventory_evidence_present`, `evidence_basis`.

5. **Bind the artifact to one asset and one run**  
   Ensure `asset_id`, `run_id`, and `ts` are all present.

6. **Do not collapse signal into state**  
   Check the wording does not imply `merged`, `frozen`, `deprecated`, or `retired` as facts.

7. **Emit the companion artifact next to the runtime result**  
   Use the run-scoped naming convention and keep it separate from Ledger/core memory.

8. **Link the two outputs explicitly**  
   Runtime result should reference the artifact path/name.

9. **Do one cold-read check**  
   Ask whether a reader would understand: runtime result = main outcome; artifact = governance observation.

10. **Abort on any hard fail**  
   Especially if Decision is polluted, evidence is incomplete, or the artifact reads like lifecycle fact.
