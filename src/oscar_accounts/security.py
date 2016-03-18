from oscar.core.loading import get_model

IPAddressRecord = get_model('oscar_accounts', 'IPAddressRecord')


def record_failed_request(request):
    record, __ = IPAddressRecord.objects.get_or_create(
        ip_address=request.META['REMOTE_ADDR'])
    record.increment_failures()


def record_successful_request(request):
    try:
        record, __ = IPAddressRecord.objects.get_or_create(
            ip_address=request.META['REMOTE_ADDR'])
    except IPAddressRecord.DoesNotExist:
        return
    record.reset()


def record_blocked_request(request):
    try:
        record, __ = IPAddressRecord.objects.get_or_create(
            ip_address=request.META['REMOTE_ADDR'])
    except IPAddressRecord.DoesNotExist:
        return
    record.increment_blocks()


def is_blocked(request):
    try:
        record = IPAddressRecord.objects.get(
            ip_address=request.META['REMOTE_ADDR'])
    except IPAddressRecord.DoesNotExist:
        record = IPAddressRecord(
            ip_address=request.META['REMOTE_ADDR'])
    return record.is_blocked()
