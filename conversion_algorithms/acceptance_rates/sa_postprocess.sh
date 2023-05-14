#!/bin/bash
# @Author: Your name
# @Date:   2023-02-08 12:10:47
# @Last Modified by:   Your name
# @Last Modified time: 2023-02-08 18:21:43
grep 'T:' sa.txt | sed 's/^.*: //' > T.txt
grep 'acceptance_rate:' sa.txt | sed 's/^.*: //' > acc_rate.txt
grep 'MSE:' sa.txt | sed 's/^.*: //' > mse.txt
