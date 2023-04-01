    with dmm:
        dmm._write("CONF:RES")
        while True:
            print(dmm._query("READ?"))
            sleep(1)
