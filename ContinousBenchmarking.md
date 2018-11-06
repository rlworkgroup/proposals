Continuous Benchmarking
=======

## Introduction:
Benchmarking an algorithm is a compute intensive and time consuming chore that is essential for guaranteeing performance. 
An algorithm can unknowingly drift towards an undesirable state if the laborious task of benchmarking is neglected for
too long.  We envision a continous benchmarking system thats runs at least nightly, and posts results for the community to see.

## Current State:
Benchmarking is currently performed manually, by running a series of benchmarking scripts that can take up
24 hours to complete.


## Our current Tools:
**Travis CI.** 
    The current CI tool to manage the workflow of building garage and executing unit tests.  The Travis CI build 
    environment have a maximum of 7.5 GB of memory, and 2 cores.  It also limits jobs to 120 minutes maximum for a
    private Github repo, and 50 minutes for a public Github repo.  
    https://docs.travis-ci.com/user/customizing-the-build/
    https://docs.travis-ci.com/user/reference/overview/

**Github Actions:**
    Each workflow can run for up to 58 minutes (including queuing and execution time).  Two workflows can be running 
    concurrently per repository.  1 virtual CPU.  Up to 3.75 GB of memory
    https://developer.github.com/actions/creating-workflows/workflow-configuration-options/

For Travis and Github actions, the compute limits are too restrictive to run the benchmarking in their environments.  
Thus, we have applied for GCP and AWS credits to spin up cloud VMs to run the benchmark jobs.  The next question would 
be whether to trigger these jobs from TravisCI/Github Actions, or to have a parallel CI system for managing the 
benchmarking.
I imagine we would have persistent VMs running, ready to receive the command to run the benchmarks.  The agent on the 
VM would then pull down the appropriate garage branch, run the benchmarks, and send the results back to another persistent machine.

## Proposed Tool:
**Teamcity:**
Enter teamcity, which provides the capabilities out of the box for the tasks described above.  The main reason for such a tool is to manage CI/CD in our own cloud, or on local machines.  This allows us to create build environments as powerful as we need.  Teamcity uses a server-agent pattern, where there is one teamcity server that manages multiple agents.  Agent software is installed on the build environments (individual cloud VM's).  Teamcity handles triggering the jobs, sending the appropriate code branch, and obtaining results.  

Teamcity has integrations for GCP and AWS that allows us to use On-Demand built agents. That is the cloud computing 
resources will be shutdown when idle in order to save on our grant credits.  If we can parallelize benchmarking jobs 
(perhaps running 'InvertedDoublePendulum-v2', 'InvertedPendulum-v2','HalfCheetah-v2', 'Hopper-v2', 'Walker2d-v2',
'Reacher-v2', 'Swimmer-v2' in separate machines), that means we can complete the job in a fraction of the time while 
using the same amount of compute credits.

We have been granted an open source License for teamcity.  I chose Teamcity because it is easier to use for me than competitors 
like Jenkins.


