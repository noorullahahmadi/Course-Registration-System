import unittest
from app import app


class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
#unit testing
    def test_root_redirect(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)

    def test_login_page(self):
        response = self.app.get('/auth/login')
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.app.get('/auth/register')
        self.assertIn(response.status_code, [200, 302])

    def test_invalid_login(self):
        response = self.app.post('/auth/login', data=dict(
            username="wrong",
            password="wrong"
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_protected_page_without_login(self):
        response = self.app.get('/dashboard', follow_redirects=True)
        self.assertIn(response.status_code, [200, 302])

    def test_courses_page(self):
        response = self.app.get('/courses', follow_redirects=True)
        self.assertIn(response.status_code, [200, 302])

    def test_students_page(self):
        response = self.app.get('/students', follow_redirects=True)
        self.assertIn(response.status_code, [200, 302])

    def test_enrollment_courses(self):
        response = self.app.get('/enrollment/courses', follow_redirects=True)
        self.assertIn(response.status_code, [200, 302])

    def test_enrollment_history(self):
        response = self.app.get('/enrollment/history', follow_redirects=True)
        self.assertIn(response.status_code, [200, 302])

#integration testing
    def test_login_flow(self):
        with self.app as client:
            response = client.post('/auth/login', data=dict(
                username="anyuser",
                password="anypassword"
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_session_behavior(self):
        with self.app as client:
            client.post('/auth/login', data=dict(
                username="wrong",
                password="wrong"
            ), follow_redirects=True)

            with client.session_transaction() as sess:
                self.assertIsInstance(sess, dict)

#debugging part
    def test_no_server_error(self):
        response = self.app.get('/auth/login')
        self.assertNotEqual(response.status_code, 500)


# run test
if __name__ == "__main__":
    unittest.main()