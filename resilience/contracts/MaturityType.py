def enum(**enums):
    return type('Enum', (), enums)

MaturityType = enum(T1=1, T2=2)
