"""
Views for the Location objects.
"""
import time
from collections import defaultdict

from pyramid.httpexceptions import (HTTPNotFound,
                                    HTTPPreconditionFailed,
                                    HTTPUnprocessableEntity)
from cornice import Service

from webgnome_api.common.session_management import (get_active_model,
                                                    get_uncertain_models,
                                                    drop_uncertain_models,
                                                    set_uncertain_models)

from webgnome_api.common.views import cors_exception, cors_policy

step_api = Service(name='step', path='/step',
                   description="Model Step API", cors_policy=cors_policy)
rewind_api = Service(name='rewind', path='/rewind',
                     description="Model Rewind API", cors_policy=cors_policy)


@step_api.get()
def get_step(request):
    '''
        Generates and returns an image corresponding to the step.
    '''
    log_prefix = 'req({0}): get_step():'.format(id(request))
    print '>>', log_prefix

    active_model = get_active_model(request)
    if active_model:
        # generate the next step in the sequence.
        gnome_sema = request.registry.settings['py_gnome_semaphore']
        gnome_sema.acquire()
        print '  ', log_prefix, 'semaphore acquired...'

        try:
            if active_model.current_time_step == -1:
                # our first step, establish uncertain models
                drop_uncertain_models(request)

                print '\thas_weathering_uncertainty', active_model.has_weathering_uncertainty
                if active_model.has_weathering_uncertainty:
                    set_uncertain_models(request)

            begin = time.time()
            output = active_model.step()

            begin_uncertain = time.time()
            steps = get_uncertain_steps(request)
            end = time.time()

            if steps and 'WeatheringOutput' in output:
                nominal = output['WeatheringOutput']
                aggregate = defaultdict(list)
                low = {}
                high = {}
                full_output = {}

                for idx, step_output in enumerate(steps):
                    for k, v in step_output['WeatheringOutput'].iteritems():
                        aggregate[k].append(v)

                for k, v in aggregate.iteritems():
                    low[k] = min(v)
                    high[k] = max(v)

                full_output = {'nominal': nominal,
                               'step_num': nominal['step_num'],
                               'time_stamp': nominal['time_stamp'],
                               'low': low,
                               'high': high}
                for idx, step_output in enumerate(steps):
                    full_output[idx] = step_output['WeatheringOutput']

                output['WeatheringOutput'] = full_output
                output['uncertain_response_time'] = end - begin_uncertain
                output['total_response_time'] = end - begin
            else:
                nominal = output['WeatheringOutput']
                full_output = {'nominal': nominal,
                               'step_num': nominal['step_num'],
                               'time_stamp': nominal['time_stamp'],
                               'low': nominal,
                               'high': nominal}
                output['WeatheringOutput'] = full_output
                output['uncertain_response_time'] = end - begin_uncertain
                output['total_response_time'] = end - begin

        except StopIteration:
            print '  ', log_prefix, 'stop iteration exception...'
            drop_uncertain_models(request)
            raise cors_exception(request, HTTPNotFound)
        except:
            print '  ', log_prefix, 'unknown exception...'
            raise cors_exception(request, HTTPUnprocessableEntity,
                                 with_stacktrace=True)
        finally:
            gnome_sema.release()
            print '  ', log_prefix, 'semaphore released...'

        return output
    else:
        raise cors_exception(request, HTTPPreconditionFailed)


@rewind_api.get()
def get_rewind(request):
    '''
        rewinds the current active Model.
    '''
    active_model = get_active_model(request)
    if active_model:
        gnome_sema = request.registry.settings['py_gnome_semaphore']
        gnome_sema.acquire()

        try:
            active_model.rewind()
        except:
            raise cors_exception(request, HTTPUnprocessableEntity,
                                 with_stacktrace=True)
        finally:
            gnome_sema.release()
    else:
        raise cors_exception(request, HTTPPreconditionFailed)


def get_uncertain_steps(request):
    uncertain_models = get_uncertain_models(request)
    if uncertain_models:
        return uncertain_models.cmd('step', {})
    else:
        return None
