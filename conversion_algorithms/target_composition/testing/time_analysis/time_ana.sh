#!/bin/bash
# @Author: Your name
# @Date:   2023-02-08 12:10:47
# @Last Modified by:   Your name
# @Last Modified time: 2023-02-24 16:01:47

grep 'MSE:' bla.txt | sed 's/^.*: //' > mse.txt
