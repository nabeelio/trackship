# trackship

"Simple" scripts that can run on cron, to log into your accounts, and export the package and shipping information. Then it can be exported to any service, such as aftership.

I run it hourly on cron on my NAS

## install

    make env
    cp config.example.yaml config.yaml
    python trackship.py
