# Pycndl:  Python Concurrent Downloader

*Pycndl* is a CLI to concurrently download multiple Web contents using multi-thread.


# Why Pycndl?

- can fast download a large number of files
- auto-retry
- log errors, stats, and progress
- easy to retry from a log
# Installation

## Pip

```bash
$ pip install git+https://github.com/hrsma2i/pycndl.git
```

# Docker

```bash
$ docker pull ghcr.io/hrsma2i/pycndl
```

Add the followings to your `~/.bashrc`.

```bash
alias cndl='docker run --rm  -v $HOME:$HOME -w $(pwd) -e GOOGLE_APPLICATION_CREDENTIALS=$HOME/.config/gcloud/application_default_credentials.json -e GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project) ghcr.io/hrsma2i/pycndl cndl'
```

```bash
$ source ~/.bashrc
```


# Usage

## CLI

```bash
$ cndl input.json ./downloaded/ 2>&1 | tee log-`date +%Y%m%d%H%M%S`.jsonlines
```

The contents whose URL is in `input.json` are downloaded to `.downloaded/`.

input.json must have `url` field like:

```json
[
    {
        "url": "http://example_1.jpg"
    },
    {
        "url": "http://example_2.png"
    },
    ...
]
```

It will work even if there are fields other than `url` or `filename`.
They will be ignored.

[JSON Lines](https://jsonlines.org/) (Newline Delimited JSON) is also supported.
Add the suffix `.jsonl` or `.jsonlines` to an input:

```bash
$ cndl input.jsonlines ./downloaded/
```

More details:

```bash
$ cndl --help
```

## Rename files

You can rename files to download, setting `filename` field:

```json
[
    {
        "url": "http://example_1.jpg",
        "filename": "foo_1.jpg"
    },
    ...
]
```

`http://example_1.jpg` will be downloaded as `./downloaded/foo_1.jpg`.


## Upload to GCS

```bash
cndl input.json gs://bucket/downloaded
```

## Retry

Failed URLs are automatically retried `--max-retry` times.

You can also retry using the log file as the next input:

```bash
$ cat log-YYYYmmddHHMMSS.jsonlines | grep 'failed to retry downloading' | jq -c {"url": .url} > input-`date +%Y%m%d%H%M%S`.jsonlines
$ cndl input-YYYYmmddHHMMSS.jsonlines ./downloaded/ 2>&1 | tee log-`date +%Y%m%d%H%M%S`.jsonlines
```


# The Number of Threads

Changing the number of threads is not supported yet.
The default numbers defined in the following document is used.

https://docs.python.org/ja/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
