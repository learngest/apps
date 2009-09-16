#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Financial functions
"""

__author__ = "Jean-Charles Bagneris <jcb@bagneris.net>"
__license__ = "BSD"

import sys

def npv(rate, cashflows):
    """
    Return NPV (float)
    rate : discount rate, float or int, in %
    cashflows : cash flows, iterable
    """
    npv = 0
    rate = rate/100.
    for year,cf in enumerate(cashflows):
        npv += cf/(1+rate)**year
    return npv

def irr(cashflows, precision=10**-4, maxrate=10**6):
    """
    Return IRR (float) in %
    cashflows : cash flows, iterable
    precision : float
    """
    binf, bsup = 0, maxrate
    while bsup - binf > precision:
        irr = (binf+bsup)/2.
        if npv(irr, cashflows) < 0:
            bsup = irr
        else:
            binf = irr
    return irr

def ytm(emission,coupon,rembt,duree):
    """
    Return YTM of bond (float) in %
    emission : issuing price
    coupon : coupon value
    rembt : repayment price
    duree : duration (years)
    WARNING - coupons are supposed to be paid yearly
    """
    cf = [-emission]
    for i in range(duree-1):
        cf.append(coupon)
    cf.append(coupon+rembt)
    print cf
    return irr(cf)


def main():
    """
    For testing purposes
    """
    cashflows = [-2000,1000,1000,500]
    print npv(10, cashflows)
    therate = irr(cashflows)
    print "%.4f %%" % therate
    print npv(therate, cashflows)
    therate = irr(cashflows, 10**-6)
    print "%.4f %%" % therate
    print npv(therate, cashflows)
    print ytm(99,5,100,10)
    return 0

if __name__ == "__main__":
    sys.exit(main())
