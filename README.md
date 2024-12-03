# graphplotter
A parser and an interactive graph plotter service with a web interface

## Supported logs
- DU nrCLI
  - `ue show link`
  - `ue show rate`
- iperf

## Starting the service
You can use any WSGI HTTP server to run the application
```bash
gunicorn app:app --bind 0.0.0.0:8050 --access-logfile access.log --error-logfile error.log --daemon
```
