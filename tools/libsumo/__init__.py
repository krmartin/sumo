# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2018-2020 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    __init__.py
# @author  Benjamin Striner
# @author  Michael Behrisch
# @date    2018-06-05

from functools import wraps
import sys
from traci import connection, constants, exceptions, _vehicle, _person, _trafficlight, _simulation
from traci.connection import StepListener 
from .libsumo import vehicle, simulation
from .libsumo import *  # noqa

_stepListeners = {}
_nextStepListenerID = 0

_traceFile = [None]

def wrapAsClassMethod(func, module):
    def wrapper(*args, **kwargs):
        return func(module, *args, **kwargs)
    return wrapper

TraCIStage.__attr_repr__ = _simulation.Stage.__attr_repr__
TraCIStage.__repr__ = _simulation.Stage.__repr__

TraCINextStopData.__attr_repr__ = _vehicle.StopData.__attr_repr__
TraCINextStopData.__repr__ = _vehicle.StopData.__repr__

TraCIReservation.__attr_repr__ = _person.Reservation.__attr_repr__
TraCIReservation.__repr__ = _person.Reservation.__repr__

TraCILogic.getPhases = _trafficlight.Logic.getPhases
TraCILogic.__repr__ = _trafficlight.Logic.__repr__

TraCIPhase.__repr__ = _trafficlight.Phase.__repr__

exceptions.TraCIException = TraCIException
simulation.Stage = TraCIStage
vehicle.StopData = TraCINextStopData
person.Reservation = TraCIReservation
trafficlight.Phase = TraCIPhase
trafficlight.Logic = TraCILogic
vehicle.addFull = vehicle.add
vehicle.addLegacy = wrapAsClassMethod(_vehicle.VehicleDomain.addLegacy, vehicle)
vehicle.couldChangeLane = wrapAsClassMethod(_vehicle.VehicleDomain.couldChangeLane, vehicle)
vehicle.wantsAndCouldChangeLane = wrapAsClassMethod(_vehicle.VehicleDomain.wantsAndCouldChangeLane, vehicle)
vehicle.isStopped = wrapAsClassMethod(_vehicle.VehicleDomain.isStopped, vehicle)
vehicle.setBusStop = wrapAsClassMethod(_vehicle.VehicleDomain.setBusStop, vehicle)
vehicle.setParkingAreaStop = wrapAsClassMethod(_vehicle.VehicleDomain.setParkingAreaStop, vehicle)
vehicle.getRightFollowers = wrapAsClassMethod(_vehicle.VehicleDomain.getRightFollowers, vehicle)
vehicle.getRightLeaders = wrapAsClassMethod(_vehicle.VehicleDomain.getRightLeaders, vehicle)
vehicle.getLeftFollowers = wrapAsClassMethod(_vehicle.VehicleDomain.getLeftFollowers, vehicle)
vehicle.getLeftLeaders = wrapAsClassMethod(_vehicle.VehicleDomain.getLeftLeaders, vehicle)
vehicle.getLaneChangeStatePretty = wrapAsClassMethod(_vehicle.VehicleDomain.getLaneChangeStatePretty, vehicle)
vehicle._legacyGetLeader = True
person.removeStages = wrapAsClassMethod(_person.PersonDomain.removeStages, person)
_trafficlight.TraCIException = TraCIException
trafficlight.setLinkState = wrapAsClassMethod(_trafficlight.TrafficLightDomain.setLinkState, trafficlight)
addStepListener = wrapAsClassMethod(connection.Connection.addStepListener, sys.modules[__name__])
removeStepListener = wrapAsClassMethod(connection.Connection.removeStepListener, sys.modules[__name__])
_manageStepListeners = wrapAsClassMethod(connection.Connection._manageStepListeners, sys.modules[__name__])


def isLibsumo():
    return True


def hasGUI():
    return False


def init(port):
    print("Warning! To make your code usable with traci and libsumo, please use traci.start instead of traci.init.")


def load(args):
    simulation.load(args)


def isLoaded():
    return simulation.isLoaded()


def simulationStep(step=0):
    simulation.step(step)
    result = []
    for domain in (edge, inductionloop, junction, lane, lanearea, multientryexit,
                   person, poi, polygon, route, trafficlight, vehicle, vehicletype):
        result += [(k, v) for k, v in domain.getAllSubscriptionResults().items()]
        result += [(k, v) for k, v in domain.getAllContextSubscriptionResults().items()]
    _manageStepListeners(step)
    return result


def getVersion():
    return simulation.getVersion()


def close():
    simulation.close()
    if _traceFile[0]:
        _traceFile[0].close()


def start(args, traceFile=None, traceGetters=True):
    if traceFile is not None:
        _startTracing(traceFile, args, traceGetters)
    simulation.load(args[1:])
    return simulation.getVersion()


def setLegacyGetLeader(enabled):
    vehicle._legacyGetLeader = enabled


def _startTracing(traceFile, cmd, traceGetters):
    _traceFile[0] = open(traceFile, 'w')
    _traceFile[0].write("traci.start(%s)\n" % repr(cmd))
    self = sys.modules[__name__]
    # simulationStep shows up as simulation.step
    for m in ["close", "load"]:
        setattr(self, m, self._addTracing(getattr(self, m)))
    for domain in [
            busstop,  # noqa
            calibrator,  # noqa
            chargingstation,  # noqa
            edge,  # noqa
            # gui,  # noqa
            inductionloop,  # noqa
            junction,  # noqa
            lanearea,  # noqa
            lane,  # noqa
            meandata,  # noqa
            multientryexit,  # noqa
            overheadwire,  # noqa
            parkingarea,  # noqa
            person,  # noqa
            poi,  # noqa
            polygon,  # noqa
            rerouter,  # noqa
            route,  # noqa
            routeprobe,  # noqa
            simulation,  # noqa
            trafficlight,  # noqa
            variablespeedsign,  # noqa
            vehicle,  # noqa
            vehicletype,  # noqa
    ]:
        for attrName in dir(domain):
            if not attrName.startswith("_"):
                attr = getattr(domain, attrName)
                if (callable(attr)
                        and attrName not in [
                            "wrapper",
                            "getAllSubscriptionResults",
                            "getAllContextSubscriptionResults",
                            "close",
                            "load",
                            "getVersion",
                ]
                        and not attrName.endswith('makeWrapper')
                        and (traceGetters or not attrName.startswith("get"))):
                    setattr(domain, attrName, _addTracing(attr, domain.__name__))


def _addTracing(method, domain=None):
    if domain:
        # replace first underscore with '.' because the methods name includes
        # the domain as prefix
        name = method.__name__.replace('_', '.', 1)
    else:
        name = method.__name__

    @wraps(method)
    def tracingWrapper(*args, **kwargs):
        _traceFile[0].write("traci.%s(%s)\n" % (
            name,
            ', '.join(list(map(repr, args)) + ["%s=%s" % (n, repr(v)) for n, v in kwargs.items()])))
        return method(*args, **kwargs)
    return tracingWrapper
