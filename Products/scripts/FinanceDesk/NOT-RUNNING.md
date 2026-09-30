Source copy of the old finance-desk scripts so that tree can leave the old repo.

Do not run them. `finance_desk.py` imports `apps.core.services.public_finance` and `stripe_poll`, which are not this function. Do not call Stripe. SQLite scripts take `--db` outside this folder. No database dump was copied.
