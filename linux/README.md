# Linux Support

Scripts, in particular init scripts, used to invoke the Python code on the Pi

To install, from this directory, run the following as root on the Pi:

```bash
cp triangula /etc/init.d/triangula
chmod a+x /etc/init.d/triangula
chmod a+x ../scripts/triangula_service.py
update-rc.d triangula defaults 
```
