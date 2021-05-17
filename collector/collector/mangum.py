from mangum import Mangum

from collector.main import app

handler = Mangum(app)
