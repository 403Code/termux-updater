import setuptools

setuptools.setup(
    author='Nanta (403Code)',
    author_email='zonenathan666@gmail.com',
    description='Tools for update termux.',
    entry_points={"console_scripts": ["termux-updater=termux_updater.bin.updater:Updater"]},
    install_requires=["requests", "bs4"],
    name='termux-updater',
    packages=setuptools.find_packages(),
    version='1.0.0'
)
