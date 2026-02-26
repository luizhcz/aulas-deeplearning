class DomainError(Exception):
    pass

class ValidationDomainError(DomainError):
    pass

class RegistryError(DomainError):
    pass

class AgentCallError(DomainError):
    pass