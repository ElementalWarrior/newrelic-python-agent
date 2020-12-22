import gc
import grpc
import pytest
import random

from testing_support.fixtures import (code_coverage_fixture,
        collector_agent_registration_fixture, collector_available_fixture)
from testing_support.mock_external_grpc_server import MockExternalgRPCServer

_coverage_source = [
    'newrelic.hooks.framework_grpc',
]

code_coverage = code_coverage_fixture(source=_coverage_source)

_default_settings = {
    'transaction_tracer.explain_threshold': 0.0,
    'transaction_tracer.transaction_threshold': 0.0,
    'transaction_tracer.stack_trace_threshold': 0.0,
    'debug.log_data_collector_payloads': True,
    'debug.record_transaction_failure': True,
}

collector_agent_registration = collector_agent_registration_fixture(
        app_name='Python Agent Test (framework_grpc)',
        default_settings=_default_settings)


@pytest.fixture(scope='module')
def grpc_app_server():
    with MockExternalgRPCServer() as server:
        yield server, server.port


@pytest.fixture(scope='module')
def mock_grpc_server(grpc_app_server):
    from sample_application.sample_application_pb2_grpc import (
            add_SampleApplicationServicer_to_server)
    from sample_application import SampleApplicationServicer
    server, port = grpc_app_server
    add_SampleApplicationServicer_to_server(
            SampleApplicationServicer(), server)
    return port


@pytest.fixture(scope='session')
def session_initialization(code_coverage, collector_agent_registration):
    pass


@pytest.fixture(scope='function')
def requires_data_collector(collector_available_fixture):
    pass


@pytest.fixture(scope='function')
def gc_garbage_empty():
    yield

    # garbage collect until everything is reachable
    while gc.collect():
        pass

    from grpc._channel import _Rendezvous
    rendezvous_stored = sum(1 for o in gc.get_objects()
            if hasattr(o, '__class__') and isinstance(o, _Rendezvous))

    assert rendezvous_stored == 0

    # make sure that even python knows there isn't any garbage remaining
    assert not gc.garbage


@pytest.fixture(scope="function")
def stub(stub_and_channel):
    return stub_and_channel[0]


@pytest.fixture(scope="function")
def stub_and_channel(mock_grpc_server):
    port = mock_grpc_server
    from sample_application.sample_application_pb2_grpc import (
            SampleApplicationStub)

    with grpc.insecure_channel('localhost:%s' % port) as channel:
        stub = SampleApplicationStub(channel)
        yield stub, channel
