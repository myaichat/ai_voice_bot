from setuptools import setup, find_packages

# Safely read the README.md file with UTF-8 encoding
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ai-voice_bot',
    version='1.0.1',
    packages=find_packages(),
    install_requires=[
        'openai',
        'websockets',
        'pyaudio',
        'numpy',
        'pydub',
        'pynput',

    ],
    entry_points={
        'console_scripts': [
            'vbot=ai_voice_bot.vbot:cli_main',
            'tbot=ai_voice_bot.tbot:cli_main',
            'mbot=ai_voice_bot.mbot:main',
        ],
    },
    include_package_data=True,
    author='Alex Buzunov',
    author_email='alex_buz@yahoo.com',
    description='An AI-powered voice bot using OpenAI Realtime API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/myaichat/ai_voice_bot',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    project_urls={
        'Source': 'https://github.com/myaichat/ai_voice_bot',
        'Tracker': 'https://github.com/myaichat/ai_voice_bot/issues',
    },
    changelog = """
    Version 1.0.1:
    - Added README.md file
    """
)