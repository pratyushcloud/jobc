
import webapp2


WIKI_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

app = webapp2.WSGIApplication([	('/jobc','jobc.MainPage')
                ,('/jobc/inviteonly/', 'jobc.InviteOnly')
                ,('/jobc/logout', 'jobc.Logout')
                ,('/jobc/realjd/_edit(/(?:[a-zA-Z0-9_-]+/?)*)', 'jobc.RealJDEdit')
                ,('/jobc/realjd(/(?:[a-zA-Z0-9_-]+/?)*)', 'jobc.RealJD')
                ,('/jobc/aboutus', 'jobc.AboutUs')
                ,('/jobc/realjob', 'jobc.ReviewDashboard')
                ,('/jobc/finance', 'jobc.Finance')
                ,('/jobc/consulting', 'jobc.Consulting')
                ,('/jobc/informationtechnology', 'jobc.IT')
                ,('/jobc/supplychain', 'jobc.SupplyChain')
                ,('/jobc/marketing', 'jobc.Marketing')
                ,('/jobc/sales', 'jobc.Sales')
				], debug=True)