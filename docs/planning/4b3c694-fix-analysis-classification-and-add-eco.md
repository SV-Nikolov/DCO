# Commit: 4b3c694 - Fix analysis classification and add ECO

Date: 2026-02-16

## Summary
- Updated analysis classification logic and supporting thresholds.
- Added ECO opening detection and minimal ECO dataset.
- Integrated opening data into analysis flow and UI display.

## Files Changed
- dco/core/analysis.py
- dco/core/classification.py
- dco/core/eco.py
- dco/data/eco_data.json
- dco/data/models.py
- dco/ui/screens/analysis.py

## Critical Notes
- ECO dataset is minimal and intended to be expanded to a full reference later.
- Opening detection uses longest-prefix matching on move sequences.
- Database schema changes include new ECO-related fields on Game records.
