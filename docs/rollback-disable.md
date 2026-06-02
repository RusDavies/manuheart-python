# Rollback and Disable Note

Status: Draft.

## Before replacing Bash Manuheart

Keep `projects/manuheart-bash` available until Python output compatibility is approved for the intended deployment.

## Disable Python one-shot usage

- Remove or disable the cron/systemd timer/wrapper that invokes `manuheart check`.
- Restore the previous Bash command if a consumer still needs reports.
- If needed, overwrite Python-generated reports with Bash-generated reports from the same config.

## Disable Python daemon usage

- Stop/disable the supervisor unit running `manuheart daemon`.
- Re-enable the previous Bash deployment or supervised one-shot path.

## Data cleanup

Generated status reports can be deleted and regenerated. Config files should not be deleted as part of rollback unless explicitly approved.
