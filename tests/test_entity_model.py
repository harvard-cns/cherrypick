import unittest
from mock import Mock
import sys

from cloudbench.env.entity.relation import *
from cloudbench.env.entity.entity_model import EntityModel
from cloudbench.env.entity import VirtualMachine

from cloudbench.env import Env
from cloudbench.env.config import EnvXmlConfig
from cloudbench import constants

class A(EntityModel):
    b_classes = depends_on_many("B")
    c_class = has_one('C')

class B(EntityModel):
    a_classes = has_many("A")
    c_class = depends_on_one('C')

class C(EntityModel):
    b_class = has_one('B')
    a_class = depends_on_one('A')


class TestRelations(unittest.TestCase):
    def setUp(self):
        self.env = Mock(spec=Env)
        self.a = A('test_a', {'a': 12}, self.env);
        self.b = B();
        self.c = C();

    def test_has_many_relation(self):
        self.assertTrue(hasattr(self.a, 'b_classes'))

        self.assertIn('b_classes', self.a.dependencies)
        self.assertNotIn('b_classes', self.a.dependents)

    def test_depends_on_many_relation(self):
        self.assertTrue(hasattr(self.b, 'a_classes'))

        self.assertIn('a_classes', self.b.dependents)
        self.assertNotIn('a_classes', self.b.dependencies)

    def test_has_one_relation(self):
        self.assertTrue(hasattr(self.c, 'a_class'))
        self.assertTrue(hasattr(self.a, 'c_class'))

        self.assertIn('c_class', self.a.dependents)
        self.assertNotIn('c_class', self.a.dependencies)

    def test_depends_on_one_relation(self):
        self.assertTrue(hasattr(self.c, 'b_class'))
        self.assertTrue(hasattr(self.b, 'c_class'))

        self.assertIn('c_class', self.b.dependencies)
        self.assertNotIn('c_class', self.b.dependents)

class TestModel(unittest.TestCase):
    def setUp(self):
        self.vm = VirtualMachine('test', {'username': "Testing"}, Mock())
        self.default_vm = VirtualMachine()

    def test_username(self):
        self.assertEqual(self.vm.username, 'Testing')
        self.assertEqual(self.default_vm.username, constants.DEFAULT_VM_USERNAME)

class TestEntityModel(unittest.TestCase):
    def setUp(self):
        self.env = Mock(spec=Env)
        self.env.config = Mock(spec=EnvXmlConfig)

        self.a = A('test_a', {'a': 12, 'bs': 'test_b'}, self.env);
        self.b = B('test_b', {'q': 12}, self.env);
        self.c = C('test_c', {'q': 12, 'a': 'test_a'}, self.env);

    @property
    def factory(self):
        return self.env.manager

    def test_relation_calls(self):
        self.env.config.get.return_value = {'test_a': self.a}
        self.assertIn(self.a, self.b.a_classes())
        self.env.config.get.assert_called_once_with('a_classes')

        self.env.reset_mock()
        self.env.config.get.return_value = {'test_b': self.b}
        self.assertIn(self.b, self.a.b_classes())
        self.env.config.get.assert_called_once_with('b_classes')

        self.env.reset_mock()
        self.env.config.get.return_value = {'test_c': self.c}
        self.assertEqual(self.c, self.a.c_class())

    def test_create(self):
        self.env.config.get.return_value = {}
        self.a.create()
        self.factory.create_a.assert_called_once_with(self.a)

        self.env.config.get.return_value = {'test_b': self.b}
        self.a.create()
        self.factory.create_b.assert_called_once_with(self.b)
        self.factory.create_a.assert_called_once_with(self.a)

    def test_delete(self):
        self.env.config.get.return_value = {}
        self.a.delete()
        self.factory.delete_a.assert_called_once_with(self.a)

        self.env.config.get.return_value = {'test_a': self.a}
        self.b.delete()
        self.factory.delete_b.assert_called_once_with(self.b)
        self.factory.delete_a.assert_called_once_with(self.a)

