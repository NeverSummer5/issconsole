# Creation date 2020-05-27
#
# Task: Implement a Python script that will accept the
# following command line arguments,
# along with any required information, and print the expected results
# loc
# print the current location of the ISS
# Example: “The ISS current location at {time} is {LAT, LONG}”
# pass
# print the passing details of the ISS for a given location
# Example: “The ISS will be overhead {LAT, LONG} at {time} for {duration}”
# people
# for each craft print the details of those people that are currently in space

from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error
import json
import click

##############################################################################
## Group og click functions
@click.group(chain=True)
def cli():
    pass

@cli.command('loc')
def make_loc():
    iss = ISSSpaceStation()
    iss.location()

@cli.command('pass')
@click.option('--lat', default=0.0, help='Latitude of the craft')
@click.option('--lon', default=0.0, help='Longitude of the craft')
def make_passing(lat, lon):
    iss = ISSSpaceStation(float(lat), float(lon))
    iss.passing(float(lat), float(lon))

@cli.command('people')
def make_people():
    iss = ISSSpaceStation()
    iss.people()

##############################################################################
# ISS space station implementation of REST API
# http://open-notify.org

class ISSSpaceStation:

    LOCATION_URL = 'http://api.open-notify.org/iss-now.json'
    PASSING_URL = 'http://api.open-notify.org/iss-pass.json'
    PEOPLE_URL = 'http://api.open-notify.org/astros.json'

    def __init__(self, latitude = 0.0, longitude = 0.0):
        self.latitude = latitude,
        self.longitude = longitude

    ##########################################################################
    # Group of methods to handle and report errors
    @staticmethod
    def request_error(re):
        click.echo(click.style(str(re.reason), fg="red"))
        exit(-1)

    @staticmethod
    def json_error(je):
        click.echo(click.style(je.msg, fg="red"))
        click.echo(click.style(je.doc, fg="red"))
        click.echo(click.style(je.pos, fg="red"))
        click.echo(click.style(je.lineno, fg="red"))
        click.echo(click.style(je.colno, fg="red"))
        exit(-1)

    @staticmethod
    def common_error(ce, obj):
        click.echo(click.style("Common error.\nError type: "
                               + ce.__class__.__name__
                               + "\nError: " + str(ce)
                               + "\nData: " + str(obj), fg="red"))
        exit(-1)

    @staticmethod
    def message_error(obj, url):
        if obj['message'] == "failure":
            click.echo(click.style(str(obj['reason']), fg="red"))
        else:
            click.echo(click.style(str('Unknown error. Url: '
                + url + " Response: " + str(obj)), fg="red"))
        exit(-1)

    ##########################################################################
    # the current location of the ISS. It returns the current
    # latitude and longitude of the space station with a unix timestamp
    # for the time the location was valid
    # http://open-notify.org/Open-Notify-API/ISS-Location-Now/
    @classmethod
    def location(cls):
        url = urllib.request.Request(cls.LOCATION_URL)
        response=""
        try: response = urllib.request.urlopen(url)
        except urllib.error.URLError as re:
            ISSSpaceStation.request_error(re)

        obj = None
        try: obj = json.loads(response.read())
        except json.JSONDecodeError as je:
            ISSSpaceStation.json_error(je)

        try:
            if obj['message'] == "success":
                timestamp = int(obj['timestampss'])
                timestamp = datetime.fromtimestamp(timestamp)
                latitude = str(obj['iss_position']['latitude'])
                longitude = str(obj['iss_position']['longitude'])

                click.echo(click.style('\nThe ISS current location'
                    , fg="bright_white",  bold=True))
                click.echo(click.style('\nTime:      {timestamp}'
                    .format(timestamp=timestamp), fg="green"))
                click.echo(click.style('Latitude:  {latitude}'
                    .format(latitude=latitude), fg="green"))
                click.echo(click.style('Longitude: {longitude}'
                    .format(longitude=longitude), fg="green"))

            else:
                ISSSpaceStation.message_error(obj, url)

        except (RuntimeError, TypeError, NameError, KeyError) as ce:
            ISSSpaceStation.common_error(ce, obj)

    ###############################################################################
    # Given a location on Earth (latitude, longitude, and altitude) this API will
    # compute the next n number of times that the ISS will be overhead.
    # http://open-notify.org/Open-Notify-API/ISS-Pass-Times/
    @classmethod
    def passing(cls, latitide, longitude):

        if latitide < -80.0 or latitide > 80.0:
            click.echo(click.style("Latitude must be number between -80.0 and 80.0"
                , fg="red"))
            exit(-1)

        if longitude < -180.0 or longitude > 180.0:
            click.echo(click.style("Longitude must be number between -180.0 and 180.0"
                , fg="red"))
            exit(-1)

        data = dict()
        data['lat'] = latitide
        data['lon'] = longitude
        url = cls.PASSING_URL + '?' + urllib.parse.urlencode(data)
        url = urllib.request.Request(url)
        response=""
        try: response = urllib.request.urlopen(url)
        except urllib.error.URLError as re:
            ISSSpaceStation.request_error(re)

        obj = None
        try: obj = json.loads(response.read())
        except json.JSONDecodeError as je:
            ISSSpaceStation.json_error(je)

        try:
            if obj['message'] == "success":

                latitude = str(obj['request']['latitude'])
                longitude = str(obj['request']['longitude'])
                passes = int(obj['request']['passes'])

                click.echo(click.style('\nThe ISS will be overhead'
                                       , fg="bright_white", bold=True))
                click.echo(click.style('\nLatitude:  {latitude}'
                                       .format(latitude=latitude), fg="green"))
                click.echo(click.style('Longitude: {longitude}'
                                       .format(longitude=longitude), fg="green"))
                click.echo(click.style('Passes: {passes}\n'
                                       .format(passes=passes), fg="green"))

                click.echo(click.style('----------------------------------------------'
                                       , fg="green"))
                click.echo(click.style('| Duration             | Risetime            |'
                                       , fg="green"))
                click.echo(click.style('-----------------------+----------------------'
                                       , fg="green"))

                for x in range(passes):
                    duration = str(obj['response'][x]['duration'])
                    risetime = int(obj['response'][x]['risetime'])
                    rs = str(datetime.fromtimestamp(risetime))

                    click.echo(click.style('| {duration: >20} | {rs: >20}|'
                                           .format(duration=duration, rs=rs), fg="green"))

            else:
                ISSSpaceStation.message_error(obj, url)

            click.echo(click.style('----------------------------------------------'
                                   , fg="green"))

        except (RuntimeError, TypeError, NameError, KeyError) as ce:
            ISSSpaceStation.common_error(ce, obj)

    ###############################################################################
    # This API returns the current number of people in space.
    # When known it also returns the names and spacecraft those people are on.
    # http://open-notify.org/Open-Notify-API/People-In-Space/
    @classmethod
    def people(cls):
        url = urllib.request.Request(cls.PEOPLE_URL)
        response = ""
        try: response = urllib.request.urlopen(url)
        except urllib.error.URLError as re:
            ISSSpaceStation.request_error(re)

        obj = None
        try: obj = json.loads(response.read())
        except json.JSONDecodeError as je:
            ISSSpaceStation.json_error(je)
        try:
            if obj['message'] == "success":
                number_of_people_in_space = int(obj['number'])

                click.echo(click.style('\nThe people now on the Space\n'
                                       , fg="bright_white", bold=True))

                click.echo(
                    click.style('----------------------------------------------'
                                       , fg="green"))
                click.echo(
                    click.style('| Name                 | Craft               |'
                                       , fg="green"))
                click.echo(
                    click.style('-----------------------+----------------------'
                                       , fg="green"))

                for i in range(number_of_people_in_space):
                    person = str(obj['people'][i]['name'])
                    craft = str(obj['people'][i]['craft'])

                    click.echo(click.style('| {person: >20} | {craft: >20}|'
                               .format(person=person, craft=craft), fg="green"))

            else:
                ISSSpaceStation.message_error(obj, url)

            click.echo(
                click.style('----------------------------------------------'
                                   , fg="green"))

        except (RuntimeError, TypeError, NameError, KeyError) as ce:
            ISSSpaceStation.common_error(ce, obj)

##############################################################################
# Entry point
if __name__ == '__main__':
    cli()
    cli.add_command(make_loc)
    cli.add_command(make_passing)
    cli.add_command(make_people)
    exit(0)
