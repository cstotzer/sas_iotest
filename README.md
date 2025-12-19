# sas_iotest - A utility to accurately measure I/O performance on unix/linux.

## Motivation 

SAS offers two utilies that allow measuring the performance of a filesystem on unix/linux:

* **iotest.sh**

    This utility has been around for a long time and is very limited as it does not allow for parallel testing and it writes files containing only zeroes which does not allow for a accurate assesment of a filesystem's write performance.

* **rhel_iotest.sh**

    While this one has some nice features like auto-scaling to the number of physical cpu's available on the host under test but, as the name suggests, can only be used on Redhat-based systems

Detailed descriptions and download links for both utilities can be found [here](https://sas.service-now.com/csm/en/testing-i-o-throughput?id=kb_article_view&sysparm_article=KB0036668).

`sas_iotest` aims to provide a lightweight, flexible alternative that:
* runs on any Unix-like system,
* has minimal dependencies,
* supports parallel and configurable workloads, and
* produces reproducible, comparable results.

## Installation

### Pre-requisites 

Running `sas_iotest.sh` requires `fio` - the Flexible I/O Tester which can be installed on most Linux flavours using the standard package manager as well as on Mac OS (using `homebrew`). As `fio` can also be installed on Windows it might also be possible to run `sas_iotest` on Windows Systems.

In order to run the companion script `collect_fio_json_to_csv.py` you will need to have Python 3.8 or greater installed. 

### Installing the script

`sas_iotest` comes with the follwing files: 

```
├── collect_fio_json_to_csv.py
├── README.md
├── run_fio_suite.sh
├── sample.env
└── fio
    ├── global.fio
    ├── mixed_50_50.fio
    ├── rand_read.fio
    ├── rand_write.fio
    ├── seq_read.fio
    └── seq_write.fio
```

* `run_fio_suite.sh` The Projects main excutable
* `collect_fio_json_to_csv.py` Create a summary table in csv-format of `fio`'s output.
*  `README.md` this document
*  `sample.env` Sample configuration
* `fio/*.fio` Configuration files for the test profiles run by `sas_iotest.sh`

Place all files into a directory which does not reside on any of the filesystem that are going to be tested. This filesystem should provide ample space to contain all the files created during the test. This directory will henceforth be refered to as `IOTEST_DIR`.

### Configuration 

Before running `sas_iotest` it needs to be configured. You will find a sample configuration in sample.env. 

Create a copy of this file named .env:

```
cp sample.env .env
```

and edit the file according to your needs. You will find description of the configuration options in `sample.env`.

Please note that the space required for running the test suite is defined by the follwing formula:

```math
SIZE\_GB * length(TESTS) * RUNS 
```

This amount must be available on the volume where `IOTEST_DIR` resides.

## Running

While the configuration step might seem daunting at first, runninig the utility is done by simply invoking the script by typing `./run_fio_suite.sh` in `IOTEST_DIR`. Configuration ensures that a test can be repeated any number of times using the same parameters whitout juggling with complex parameter lists on the command line.

Running `sas_iotest.sh` will create a directory `work` to contain the files used for testing and a directory `output` to hold the files containing the test results. 

After `sas_iotest` has been run, running `python3 collect_fio_json_to_csv.py` will produce a summary table in the file `fio_summary.csv`. This file can be imported to excel for analysis or graphical representation.

## How to interpret the results

Sample output:

```
target,test,n_runs,read_mb_s_avg,write_mb_s_avg,read_iops_avg,write_iops_avg,read_lat_us_avg,write_lat_us_avg
nvme,mixed_50_50,3,1752.9,1848.2,7011.7,7392.9,0.0,0.0
nvme,rand_read,3,6319.8,0.0,1617870.3,0.0,0.0,0.0
nvme,rand_write,3,0.0,2384.1,0.0,610327.0,0.0,0.0
nvme,seq_read,3,21332.0,0.0,85328.1,0.0,0.0,0.0
nvme,seq_write,3,0.0,8128.2,0.0,32512.8,0.0,0.0
sata,mixed_50_50,3,1794.0,1890.1,7176.0,7560.5,0.0,0.0
sata,rand_read,3,10004.5,0.0,2561163.4,0.0,0.0,0.0
sata,rand_write,3,0.0,3152.7,0.0,807095.3,0.0,0.0
sata,seq_read,3,30936.3,0.0,123745.1,0.0,0.0,0.0
sata,seq_write,3,0.0,8117.0,0.0,32468.0,0.0,0.0
```


Each row represents the average of multiple runs (n_runs) for a specific storage target and workload type. The metrics are already aggregated and comparable across targets.

Key dimensions
* target

  Logical name of the tested storage backend (e.g. nvme, sata).
* test
    
    I/O access pattern:
    * seq_read, seq_write – large, sequential I/O
    * rand_read, rand_write – small, random I/O
    * mixed_50_50 – 50% read / 50% write mix
* n_runs
  
  Number of repetitions used to compute the averages. Higher values improve stability.

### Performance metrics

#### Throughput (MB/s)
read_mb_s_avg / write_mb_s_avg
Best indicator for sequential workloads such as:
data scans
backups
large file transfers
Example interpretation:
seq_read: SATA shows higher throughput than NVMe → likely sequential bandwidth–limited, not latency-limited.
seq_write: both targets show similar write bandwidth → write path may be capped elsewhere (controller, filesystem, sync behavior).

#### IOPS
* read_iops_avg / write_iops_avg
  
  Most relevant for random workloads, typical for:
  * databases
  * metadata-heavy applications
  * many small files

#### Latency metrics
* read_lat_us_avg / write_lat_us_avg

  Average completion latency in microseconds.
