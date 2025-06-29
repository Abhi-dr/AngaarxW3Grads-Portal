# Local Setup Guide

## Todo
## Prerequisites

Before you begin, ensure you have met the following requirements:
- You have installed the latest version of [Python](https://www.python.org/)
- You have a working [Git](https://git-scm.com/) installation
- You have a code editor like [VS Code](https://code.visualstudio.com/)

## Installation

Follow these steps to set up the project locally:

1. **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/AngaarxW3Grads-Portal.git
    ```
2. **Navigate to the project directory:**
    ```bash
    cd AngaarxW3Grads-Portal
    ```
3. **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```
4. **Activate the virtual environment:**
    - On Windows:
        ```bash
        venv\Scripts\activate
        ```
    - On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
5. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Project

To run the project locally, use the following command:
```bash
python manage.py runserver
```
The application should now be running on [http://localhost:8000](http://localhost:8000).

## Testing

To run tests, use the following command:
```bash
python manage.py test
```

## Contributing

To contribute to this project, follow these steps:

1. Fork the repository.
2. Create a new branch:
    ```bash
    git checkout -b feature-branch
    ```
3. Make your changes and commit them:
    ```bash
    git commit -m 'Add some feature'
    ```
4. Push to the branch:
    ```bash
    git push origin feature-branch
    ```
5. Create a pull request.

## Contact

If you have any questions, please contact [your-email@example.com](mailto:your-email@example.com).

## License

This project is licensed under the [MIT License](LICENSE).

## Additional Setup Steps

### Setting Up Environment Variables

1. **Create a `.env` file** in the root directory of the project and add the necessary environment variables. Here is an example of what your `.env` file might look like:
    ```env
    DEBUG=True
    SECRET_KEY=your_secret_key
    DATABASE_URL=your_database_url
    ```

### Handling Redis Error on Windows

If you encounter a Redis error on Windows, you will need to set up Windows Subsystem for Linux (WSL). Follow the instructions in the [WSL Installation Guide](https://docs.microsoft.com/en-us/windows/wsl/install) to install WSL and set up Redis.

### Setting Up Database Connection

1. **Use MySQL Workbench** or any other database management tool to set up the database connection. Ensure that the credentials in your `.env` file match the database configuration.

### Installing Requirements

Make sure to install the required dependencies:
```bash
pip install -r requirements.txt
```

