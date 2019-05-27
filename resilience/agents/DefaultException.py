def enum(**enums):
    return type('Enum', (), enums)


class DefaultException(Exception):
    TypeOfDefault = enum(LIQUIDITY=1, SOLVENCY=2, FAILED_MARGIN_CALL=3)

    def __init__(self, me, typeOfDefault):
        self.me = me
        self.typeOfDefault = typeOfDefault
        self.timestep = me.get_time()
        # PERF these measures are commented out to speed up the simulation
        # since they are not used at all
        # TODO maybe remove these lines
        # self.equityAtDefault = me.get_equity_valuation()
        # if hasattr(me, 'isaBank') and me.isaBank:
        #     self.lcrAtDefault = me.get_LCR()

    def get_agent(self):
        return self.me

    def get_type_of_default(self):
        return self.typeOfDefault

    def get_timestep(self):
        return self.timestep
