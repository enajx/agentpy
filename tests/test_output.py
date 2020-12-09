import pytest
import agentpy as ap
import pandas as pd
import shutil
import os

from agentpy.tools import AgentpyError


class AgentType1(ap.Agent):
    def setup(self):
        self.x = 'x1'

    def action(self):
        self.record('x')


class AgentType2(AgentType1):
    def setup(self):
        self.x = 'x2'
        self.y = 'y2'

    def action(self):
        self.record(['x', 'y'])


class EnvType3(ap.Environment):
    def setup(self):
        self.x = 'x3'
        self.z = 'z4'

    def action(self):
        self.record(['x', 'z'])


class EnvType4(ap.Environment):
    def setup(self):
        self.z = 'z4'

    def action(self):
        self.record(['z'])


class ModelType0(ap.Model):

    def setup(self):
        self.add_env('E31', env_class=EnvType3)
        self.add_env(['E41', 'E42'], env_class=EnvType4)
        self.envs.add_agents(agents=2, agent_class=AgentType1)
        self.E42.add_agents(agents=2, agent_class=AgentType2)

    def step(self):
        self.agents.action()
        for env in self.envs.values():
            env.action()  # TODO Change after EnvDict improvements

    def end(self):
        self.measure('m_key', 'm_value')


def test_testing_model():

    parameters = {'steps': 2, 'px': (1, 2)}
    sample = ap.sample_discrete(parameters)
    settings = {'iterations': 2,
                'scenarios': ['test1', 'test2'],
                'record': True}

    model = ModelType0(sample[0])
    pytest.model_results = model_results = model.run(display=False)

    exp = ap.Experiment(ModelType0, sample, **settings)
    pytest.exp_results = exp_results = exp.run(display=False)

    type_list = ['AgentType1', 'AgentType2', 'EnvType3', 'EnvType4']
    assert list(model_results.variables.keys()) == type_list
    assert list(exp_results.variables.keys()) == type_list


def arrange_things(results):

    return (results.arrange(variables='x'),
            results.arrange(variables=['x']),
            results.arrange(variables=['x', 'y']),
            results.arrange(variables='z'),
            results.arrange(parameters='px'),
            results.arrange(measures='m_key'),
            results.arrange(variables='all',
                            parameters='all',
                            measures='all'))


def test_datadict_arrange_for_single_run():

    results = pytest.model_results
    data = arrange_things(results)
    x_data, x_data2, xy_data, z_data, p_data, m_data, all_data = data

    assert x_data.equals(x_data2)
    assert list(x_data['x']) == ['x1'] * 4 + ['x2'] * 4 + ['x3'] * 2

    assert x_data.shape == (10, 4)
    assert xy_data.shape == (10, 5)
    assert z_data.shape == (6, 4)
    assert p_data.shape == (1, 2)
    assert m_data.shape == (1, 2)
    assert all_data.shape == (15, 10)


def test_datadict_arrange_for_multi_run():

    results = pytest.exp_results
    data = arrange_things(results)
    x_data, x_data2, xy_data, z_data, p_data, m_data, all_data = data

    assert x_data.equals(x_data2)
    assert x_data.shape == (80, 6)
    assert xy_data.shape == (80, 7)
    assert z_data.shape == (48, 6)
    assert p_data.shape == (4, 2)
    assert m_data.shape == (8, 3)
    assert all_data.shape == (120, 11)


def test_datadict_arrange_measures():

    results = pytest.exp_results
    mvp_data = results.arrange(measures='all', parameters='varied')
    mvp_data_2 = results.arrange_measures()
    assert mvp_data.equals(mvp_data_2)


def test_datadict_save_and_load():

    results = pytest.exp_results
    results.save()
    loaded = ap.load('ModelType0')
    shutil.rmtree('ap_output')

    for key, item in results.items():
        if isinstance(item, pd.DataFrame):
            assert loaded[key].equals(results[key])
        elif isinstance(item, ap.DataDict):
            for k, i in item.items():
                if isinstance(i, pd.DataFrame):
                    assert loaded[key][k].equals(results[key][k])
                else:
                    assert loaded[key][k] == results[key][k]
        else:
            assert loaded[key] == results[key]
