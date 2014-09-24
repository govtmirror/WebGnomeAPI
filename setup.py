"""
    Setup file.
"""
import os
import shutil
import fnmatch

from setuptools import setup, find_packages
from distutils.command.clean import clean

# could run setup from anywhere
here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

requires = ['cornice',
            'waitress',
            'WebTest',
            'webhelpers2>=2.0b5',
            'pyramid_redis_sessions>=1.0a1',
            'awesome-slugify',
            'GDAL']


class cleandev(clean):
    description = 'cleans files generated by develop mode'

    def run(self):
        # call base class clean
        clean.run(self)

        # clean auto-generated files
        paths = [os.path.join(here, 'webgnome_api'),
                 ]
        file_patterns = ['*.pyc']

        for path in paths:
            for pattern in file_patterns:
                file_list = [os.path.join(dirpath, f)
                             for dirpath, dirnames, files in os.walk(path)
                             for f in fnmatch.filter(files, pattern)]

                for f in file_list:
                    try:
                        os.remove(f)
                        print "Deleted auto-generated file: {0}".format(f)
                    except OSError as err:
                        print ("Failed to remove {0}. Error: {1}"
                               .format(f, err))

        rm_dir = ['webgnome_api.egg-info']
        for dir_ in rm_dir:
            try:
                shutil.rmtree(dir_)
                print "Deleted auto-generated directory: {0}".format(dir_)
            except OSError as err:
                if err.errno != 2:
                    # we report everything except file not found.
                    print ("Failed to remove {0}. Error: {1}"
                           .format(dir_, err))


setup(name='webgnome_api',
      version=0.1,
      description='webgnome_api',
      long_description=README,
      classifiers=["Programming Language :: Python",
                   "Framework :: Pylons",
                   "Topic :: Internet :: WWW/HTTP",
                   "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
                   ],
      keywords="adios gnome oilspill weathering trajectory modeling",
      author='ADIOS/GNOME team at NOAA ORR',
      author_email='orr.gnome@noaa.gov',
      url='',
      cmdclass={'cleandev': cleandev,
                },
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite='webgnome_api',
      entry_points=('[paste.app_factory]\n'
                    '  main = webgnome_api:main\n'),
)
