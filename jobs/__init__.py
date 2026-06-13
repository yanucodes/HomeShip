"""Standalone scheduled jobs, decoupled from any particular scheduler.

Each module here is runnable as `python -m jobs.<name>` so the trigger
(Render Cron, system cron, a one-off manual run) stays a swappable detail.
"""
