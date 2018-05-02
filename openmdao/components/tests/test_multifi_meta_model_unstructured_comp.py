import numpy as np
import unittest

from openmdao.api import Group, Problem, MultiFiMetaModelUnStructuredComp, MultiFiSurrogateModel, \
     MultiFiCoKrigingSurrogate
from openmdao.utils.assert_utils import assert_rel_error


class MockSurrogate(MultiFiSurrogateModel):

    def __init__(self):
        super(MockSurrogate, self).__init__()
        self.xtrain = None
        self.ytrain = None

    def train_multifi(self, x, y):
        self.xtrain = x
        self.ytrain = y

    def predict(self, x):
        self.xpredict = x
        return 0.0


class MultiFiMetaModelTestCase(unittest.TestCase):

    def test_inputs_wrt_nfidelity(self):
        mm = MultiFiMetaModelUnStructuredComp(nfi=3)

        mm.add_input('x', 0.)
        mm.add_output('y', 0.)

        prob = Problem(Group())
        prob.model.add_subsystem('mm', mm)
        prob.setup(check=False)

        self.assertEqual(mm.metadata['train:x'], None)
        self.assertEqual(mm.metadata['train:x_fi2'], None)
        self.assertEqual(mm.metadata['train:x_fi3'], None)
        self.assertEqual(mm.metadata['train:y'], None)
        self.assertEqual(mm.metadata['train:y_fi2'], None)
        self.assertEqual(mm.metadata['train:y_fi3'], None)

    def test_one_dim_one_fidelity_training(self):
        mm = MultiFiMetaModelUnStructuredComp()
        surr = MockSurrogate()

        mm.add_input('x', 0.)
        mm.add_output('y', 0., surrogate=surr)

        prob = Problem(Group())
        prob.model.add_subsystem('mm', mm)
        prob.setup(check=False)

        mm.metadata['train:x'] = [0.0, 0.4, 1.0]
        mm.metadata['train:y'] = [3.02720998, 0.11477697, 15.82973195]

        expected_xtrain=[np.array([[0.0], [0.4], [1.0]])]
        expected_ytrain=[np.array([[3.02720998], [0.11477697], [15.82973195]])]

        prob.run_model()
        np.testing.assert_array_equal(surr.xtrain, expected_xtrain)
        np.testing.assert_array_equal(surr.ytrain, expected_ytrain)

        expected_xpredict=0.5
        prob['mm.x'] = expected_xpredict
        prob.run_model()

        np.testing.assert_array_equal(surr.xpredict, expected_xpredict)

    def test_one_dim_bi_fidelity_training(self):
        mm = MultiFiMetaModelUnStructuredComp(nfi=2)
        surr = MockSurrogate()

        mm.add_input('x', 0.)
        mm.add_output('y', 0., surrogate=surr)

        prob = Problem(Group())
        prob.model.add_subsystem('mm', mm)
        prob.setup(check=False)

        mm.metadata['train:x']= [0.0, 0.4, 1.0]
        mm.metadata['train:x_fi2'] = [0.1, 0.2, 0.3, 0.5, 0.6,
                                  0.7, 0.8, 0.9, 0.0, 0.4, 1.0]
        mm.metadata['train:y'] = [3.02720998, 0.11477697, 15.82973195]
        mm.metadata['train:y_fi2'] = [-9.32828839, -8.31986355, -7.00778837,
                                  -4.54535129, -4.0747189 , -5.30287702,
                                  -4.47456522, 1.85597517, -8.48639501,
                                  -5.94261151, 7.91486597]
        expected_xtrain=[np.array([[0.0], [0.4], [1.0]]),
                         np.array([[0.1], [0.2], [0.3], [0.5], [0.6], [0.7],
                                   [0.8], [0.9], [0.0], [0.4], [1.0]])]
        expected_ytrain=[np.array([[ 3.02720998], [0.11477697], [15.82973195]]),
                         np.array([[-9.32828839], [-8.31986355], [-7.00778837], [-4.54535129],
                                   [-4.0747189],  [-5.30287702], [-4.47456522], [1.85597517],
                                   [-8.48639501], [-5.94261151], [7.91486597]])]
        prob.run_model()
        np.testing.assert_array_equal(surr.xtrain[0], expected_xtrain[0])
        np.testing.assert_array_equal(surr.xtrain[1], expected_xtrain[1])
        np.testing.assert_array_equal(surr.ytrain[0], expected_ytrain[0])
        np.testing.assert_array_equal(surr.ytrain[1], expected_ytrain[1])

    def test_two_dim_bi_fidelity_training(self):
        mm = MultiFiMetaModelUnStructuredComp(nfi=2)
        surr_y1 = MockSurrogate()
        surr_y2 = MockSurrogate()

        mm.add_input('x1', 0.)
        mm.add_input('x2', 0.)
        mm.add_output('y1', 0., surrogate=surr_y1)
        mm.add_output('y2', 0., surrogate=surr_y2)

        prob = Problem(Group())
        prob.model.add_subsystem('mm', mm)
        prob.setup(check=False)

        mm.metadata['train:x1']     = [1.0, 2.0, 3.0]
        mm.metadata['train:x1_fi2'] = [1.1, 2.1, 3.1, 1.0, 2.0, 3.0]
        mm.metadata['train:x2']     = [1.0, 2.0, 3.0]
        mm.metadata['train:x2_fi2'] = [2.1, 2.2, 2.3, 1.0, 2.0, 3.0]
        mm.metadata['train:y1']     = [0.0, 0.1, 0.2]
        mm.metadata['train:y1_fi2'] = [3.0, 3.1, 3.3, 3.4, 3.5 ,3.6]
        mm.metadata['train:y2']     = [4.0, 4.0, 4.0]
        mm.metadata['train:y2_fi2'] = [4.0, 4.1, 4.3, 4.4, 4.5 ,4.6]

        prob.run_model()
        expected_xtrain=[np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]]),
                         np.array([[1.1, 2.1], [2.1, 2.2], [3.1, 2.3],
                                   [1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])]
        expected_y1train=[np.array([[0.0], [0.1], [0.2]]),
                          np.array([[3.0], [3.1], [3.3], [3.4], [3.5], [3.6]])]
        expected_y2train=[np.array([[4.0], [4.0], [4.0]]),
                          np.array([[4.0], [4.1], [4.3], [4.4], [4.5], [4.6]])]

        np.testing.assert_array_equal(surr_y1.ytrain[0], expected_y1train[0])
        np.testing.assert_array_equal(surr_y1.ytrain[1], expected_y1train[1])
        np.testing.assert_array_equal(surr_y2.ytrain[0], expected_y2train[0])
        np.testing.assert_array_equal(surr_y2.ytrain[1], expected_y2train[1])
        np.testing.assert_array_equal(surr_y1.ytrain[0], expected_y1train[0])
        np.testing.assert_array_equal(surr_y1.ytrain[1], expected_y1train[1])
        np.testing.assert_array_equal(surr_y2.ytrain[0], expected_y2train[0])
        np.testing.assert_array_equal(surr_y2.ytrain[1], expected_y2train[1])

    def test_array_multi_vectorize(self):
        def branin(x):
            x1 = 15*x[0]-5
            x2 = 15*x[1]
            return (x2-(5.1/(4.*np.pi**2.))*x1**2.+5.*x1/np.pi-6.)**2.+10.*(1.-1./(8.*np.pi))*np.cos(x1)+10.

        # Add a linear error
        def branin_low_fidelity(x):
            return branin(x)+30.*x[1] + 10.

        mm = MultiFiMetaModelUnStructuredComp(nfi=2)
        mm.add_input('x', np.zeros((1, 2)))
        mm.add_output('y', np.zeros((1, )))
        mm.default_surrogate = MultiFiCoKrigingSurrogate()

        prob = Problem()
        prob.model.add_subsystem('mm', mm)
        prob.setup(check=False)

        x = [[[ 0.13073587,  0.24909577],  # expensive (hifi) doe
              [ 0.91915571,  0.4735261 ],
              [ 0.75830543,  0.13321705],
              [ 0.51760477,  0.34594101],
              [ 0.03531219,  0.77765831],
              [ 0.27249206,  0.5306115 ],
              [ 0.62762489,  0.65778471],
              [ 0.3914706 ,  0.09852519],
              [ 0.86565585,  0.85350002],
              [ 0.40806563,  0.91465314]],

             [[ 0.91430235,  0.17029894],  # cheap (lowfi) doe
              [ 0.99329651,  0.76431519],
              [ 0.2012252 ,  0.35006032],
              [ 0.61707854,  0.90210676],
              [ 0.15113004,  0.0133355 ],
              [ 0.07108082,  0.55344447],
              [ 0.4483159 ,  0.52182902],
              [ 0.5926638 ,  0.06595122],
              [ 0.66305449,  0.48579608],
              [ 0.47965045,  0.7407793 ],
              [ 0.13073587,  0.24909577],  # notice hifi doe inclusion
              [ 0.91915571,  0.4735261 ],
              [ 0.75830543,  0.13321705],
              [ 0.51760477,  0.34594101],
              [ 0.03531219,  0.77765831],
              [ 0.27249206,  0.5306115 ],
              [ 0.62762489,  0.65778471],
              [ 0.3914706 ,  0.09852519],
              [ 0.86565585,  0.85350002],
              [ 0.40806563,  0.91465314]]]
        y = np.array([[branin(case) for case in x[0]],
                      [branin_low_fidelity(case) for case in x[1]]])

        mm.metadata['train:x'] = x[0]
        mm.metadata['train:y'] = y[0]
        mm.metadata['train:x_fi2'] = x[1]
        mm.metadata['train:y_fi2'] = y[1]

        prob['mm.x'] = np.array([[2./3., 1./3.]])
        prob.run_model()

        assert_rel_error(self, prob['mm.y'], 26, tolerance=0.02)

        prob['mm.x'] = np.array([[1./3., 2./3.]])
        prob.run_model()

        assert_rel_error(self, prob['mm.y'], 36.1031735, tolerance=0.02)

        # Now, vectorized model with both points predicted together.

        mm = MultiFiMetaModelUnStructuredComp(nfi=2, vec_size=2)
        mm.add_input('x', np.zeros((2, 1, 2)))
        mm.add_output('y', np.zeros((2, 1, )))
        mm.default_surrogate = MultiFiCoKrigingSurrogate()

        prob = Problem()
        prob.model.add_subsystem('mm', mm)
        prob.setup(check=False)

        mm.metadata['train:x'] = x[0]
        mm.metadata['train:y'] = y[0]
        mm.metadata['train:x_fi2'] = x[1]
        mm.metadata['train:y_fi2'] = y[1]

        prob['mm.x'] = np.array([[[2./3., 1./3.]], [[1./3., 2./3.]]])
        prob.run_model()

        assert_rel_error(self, prob['mm.y'], [26, 36.1031735], tolerance=0.02)

    def test_multifi_meta_model_unstructured_deprecated(self):
        # run same test as above, only with the deprecated component,
        # to ensure we get the warning and the correct answer.
        # self-contained, to be removed when class name goes away.
        from openmdao.components.multifi_meta_model_unstructured_comp import MultiFiMetaModelUnStructured  # deprecated
        import warnings

        with warnings.catch_warnings(record=True) as w:
            mm = MultiFiMetaModelUnStructured(nfi=3)

        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[0].category, DeprecationWarning))
        self.assertEqual(str(w[0].message), "'MultiFiMetaModelUnStructured' has been deprecated. Use "
                                            "'MultiFiMetaModelUnStructuredComp' instead.")

        mm.add_input('x', 0.)
        mm.add_output('y', 0.)

        prob = Problem(Group())
        prob.model.add_subsystem('mm', mm)
        prob.setup(check=False)

        self.assertEqual(mm.metadata['train:x'], None)
        self.assertEqual(mm.metadata['train:x_fi2'], None)
        self.assertEqual(mm.metadata['train:x_fi3'], None)
        self.assertEqual(mm.metadata['train:y'], None)
        self.assertEqual(mm.metadata['train:y_fi2'], None)
        self.assertEqual(mm.metadata['train:y_fi3'], None)

    def test_multifi_meta_model_unstructured_deprecated(self):
        # run same test as above, only with the deprecated component,
        # to ensure we get the warning and the correct answer.
        # self-contained, to be removed when class name goes away.
        from openmdao.components.multifi_meta_model_unstructured_comp import MultiFiMetaModel  # deprecated
        import warnings

        with warnings.catch_warnings(record=True) as w:
            mm = MultiFiMetaModel(nfi=3)

        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[0].category, DeprecationWarning))
        self.assertEqual(str(w[0].message), "'MultiFiMetaModel' component has been deprecated. Use "
                                            "'MultiFiMetaModelUnStructuredComp' instead.")

        mm.add_input('x', 0.)
        mm.add_output('y', 0.)

        prob = Problem(Group())
        prob.model.add_subsystem('mm', mm)
        prob.setup(check=False)

        self.assertEqual(mm.metadata['train:x'], None)
        self.assertEqual(mm.metadata['train:x_fi2'], None)
        self.assertEqual(mm.metadata['train:x_fi3'], None)
        self.assertEqual(mm.metadata['train:y'], None)
        self.assertEqual(mm.metadata['train:y_fi2'], None)
        self.assertEqual(mm.metadata['train:y_fi3'], None)

if __name__ == "__main__":
    unittest.main()
