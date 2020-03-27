Slackexceptions = {'SlackChannelException': {'enum': 200, 'emsg': 'Slack channel is invalid. Rerun user_setup'},
                   'SlackTokenException': {'enum': 201, 'emsg': 'Slack token is invalid. Rerun user_setup'}}


class SlackExceptions(Exception):
    pass


class SlackChannelException(SlackExceptions):
    message = Slackexceptions["SlackChannelException"]["emsg"]
    eNumber = Slackexceptions["SlackChannelException"]["enum"]

class SlackTokenException(SlackExceptions):
    message = Slackexceptions["SlackTokenException"]["emsg"]
    eNumber = Slackexceptions["SlackTokenException"]["enum"]
    pass
