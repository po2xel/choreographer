# Devtools Protocol

`pip install devtools` not released yet!

`devtools` allows remote control of browsers (currently only chrome-ish) from python. Python's async/await is strongly recommended and supported, but not required.

### ⚠️⚠️⚠️**Testers Needed!**⚠️⚠️⚠️

**This package is cross-platform and testing on _many various platforms_ will help us! See [here](#%EF%B8%8F-help-needed-%EF%B8%8F).**


## Quickstart (asyncio)

Easy:
```python
import asyncio
import devtools


async with Browser(headless=False) as browser:
	new_tab = await browser.create_tab("https://google.com")
	await asyncio.sleep(3)
	await new_tab.send_command("Page.navigate", params=dict(url="https://github.com"))
	await asyncio.sleep(3)
```

See [the devtools reference](https://chromedevtools.github.io/devtools-protocol/) for a list of all possible commands.

### Subscribing to Events

```python
	... # continued from above

	# Callback for printing result
	async def dump_event(response):
		print(str(response))

	# Callback for raising result as error
	async def error_event(response):
		raise Exception(str(response))

	browser.subscribe("Target.targetCrashed", error_event)
	new_tab.subscribe("Page.loadEventFired", dump_event)
	browser.subscribe("Target.*", dump_event) # dumps all "Target" events
	reponse = await new_tab.subscribe_once("Page.lifecycleEvent")
	# do something with response
	browser.unsubscribe("Target.*")
	# events are always sent to a browser or tab, but the documentation isn't always clear which
	# so dumping all: `browser.subscribe("*", dump_event)` can be useful (but verbose) for debugging
```
Install this repository (`pip install .`) and `numpy`.

## Other Options

### Non-asyncio

You can use this library without `asyncio`,
```
my_browser = devtools.Browser()
```
But you are responsible for calling all `browser.pipe.read_jsons(blocking=True|False)` and organizing the results. `browser.run_output_thread()` will start a second thread that constantly prints all responses from the browser, it can't be used with `asyncio`- it won't play nice with any other read.

### Low-level use

We provide a `Browser` and `Tab` interface, but there is also a lower-level `Target` and `Session` interface that one can use if needed.

--------------------------
--------------------------
--------------------------
--------------------------
# ⚠️ Help Needed! ⚠️

### First Test

Please run: `python app/test1.py` and send me the output along with information about your browser, operating system, and python. Internal plotly slack is fine #kaleido, or a github issue is also fine.

#### Optional Tests

Run: `app/app.py` and send me the output.

If everything works, feel free to give `kaleido/app.py` a shot.
