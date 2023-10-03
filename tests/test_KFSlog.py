# Copyright (c) 2023 구FS, all rights reserved. Subject to the LICENCE NAME licence in `licence.md`.
import datetime as dt
import hypothesis, hypothesis.strategies
import inspect
from KFSfstr import KFSfstr
import logging
import os
import random
import re
import sys
import time

sys.path.append("./")   # enables importing via parent directory
from KFSlog.KFSlog import setup_logging
from KFSlog.KFSlog import timeit


@hypothesis.given(hypothesis.strategies.text(), hypothesis.strategies.integers(), hypothesis.strategies.booleans(), hypothesis.strategies.booleans())
def test_setup_logging(logger_name: str, logging_level: int, print_to_console: bool, print_to_logfile: bool) -> None:
    logger: logging.Logger
    
    
    logger=setup_logging(logger_name, logging_level, print_to_console=print_to_console, print_to_logfile=print_to_logfile)
    if random.choice([True, False]):
        logger=setup_logging(logger_name, logging_level, print_to_console=print_to_console, print_to_logfile=print_to_logfile)  # randomly check that setup_logging can be called twice without error


    if logger_name=="":                                                         # if logger name given is empty:
        assert logger.name=="root"                                              # check that logger name is root
    else:
        assert logger.name==logger_name                                         # check that logger name matches
    assert logger.level==logging_level                                          # check that logger level matches
    assert len(logger.handlers)==int(print_to_console)+int(print_to_logfile)    # check that number of handlers matches number of print destinations

    # TODO redirect stdout to file and check logger outputs (console and file) under different conditions
    
    return


@hypothesis.settings(deadline=dt.timedelta(seconds=4))
@hypothesis.given(hypothesis.strategies.integers(min_value=1, max_value=3), hypothesis.strategies.booleans())   # don't sleep 0s, because duration parsing from log file does not support durations of µs, ms, etc
def test_timeit(sleep: int, f_fails: bool) -> None:
    DURATION_MESSAGE_PATTERN: str=r"^(( )*Duration: (?P<duration>[0-9]{1,3}(,[0-9]{1,3})?)s)$"
    duration: float # actual execution time
    log: list[str]
    now_dt: dt.datetime=dt.datetime.now(dt.timezone.utc)
    result: None    # f result

    class Specific_Exception(Exception):
        pass


    setup_logging("", logging.INFO) # setup logging, the implicit setup seems to be unreliable


    @timeit
    def f() -> None:
        time.sleep(sleep)
        if f_fails==True:
            raise Specific_Exception("f failed.")
        return

    try:
        result=f()
    except Specific_Exception as e:
        assert f_fails==True            # check that f was supposed to fail
        assert e.args[0]=="f failed."   # check that error message is preserved
    except:                             # if other exception:
        assert False                    # should not happen
    else:                               # if successful:
        assert f_fails==False           # check that f was not supposed to fail
        assert result==None             # check that result is None

    assert os.path.isfile(f"./log/{now_dt.strftime("%Y-%m-%d")}.log")                   # check that log file exists
    with open(f"./log/{now_dt.strftime("%Y-%m-%d")}.log", "rt") as log_file:
        log=log_file.read().split("\n")
    assert 4<=len(log)                                                                  # check that at least the 2 log messages from this test are in the log, 4 lines because of duration has own line and empty line at end
    assert log[-4].endswith(f"INFO Executing {f.__name__}{inspect.signature(f)}...")    # check that log messages are correct
    if f_fails==True:
        assert log[-3].endswith(f"ERROR Executing {f.__name__}{inspect.signature(f)} failed with test_KFSlog.Specific_Exception.")
    else:
        assert log[-3].endswith(f"INFO Executed {f.__name__}{inspect.signature(f)} = {str(result)}.") # type:ignore
    
    re_match=re.search(DURATION_MESSAGE_PATTERN, log[-2])
    assert re_match!=None
    duration=float(re_match.groupdict()["duration"].replace(",", "."))
    assert abs(duration-sleep)<=0.1 # check that duration is within 100ms of sleep time

    return