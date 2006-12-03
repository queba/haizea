from pysqlite2 import dbapi2 as sqlite


class ReservationDB(object):
    def __init__(self):
        pass
    
    def printReservations(self):
        conn = self.getConn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM V_ALLOCATION")
        
        for row in cur:
            print row
    
    def getConn(self):
        return None
    
    def existsRemainingReservations(self, afterTime):
        sql = "SELECT COUNT(*) FROM tb_alloc WHERE all_schedend >= ?"
        cur = self.getConn().cursor()
        cur.execute(sql, (afterTime,))
        count = cur.fetchone()[0]

        if count == 0:
            return False
        else:
            return True

    def getAllocationsInInterval(self, time, eventfield, td=None, distinct=None, allocstatus=None, res=None, sl_id=None):
        if distinct==None:
            sql = "SELECT * FROM v_allocation"
        else:
            sql = "SELECT DISTINCT"
            for field in distinct:
                sql += " %s," % field
            sql=sql[:-1]
            sql += " FROM v_allocation" 
                
        if td != None:
            sql += " WHERE %s >= ? AND %s < ?" % (eventfield, eventfield)        
        else:
            sql += " WHERE %s >= ? " % (eventfield)        

        if allocstatus != None:
            sql += " AND all_status = %i" % allocstatus

        if res != None:
            sql += " AND res_id = %i" % res

        if sl_id != None:
            sql += " AND sl_id = %i" % sl_id

        cur = self.getConn().cursor()
        if td != None:
            cur.execute(sql, (time, time+td))
        else:
            cur.execute(sql, (time,))

        return cur        

    def findAvailableSlots(self, time, amount=None, type=None, slots=None, closed=True):
        if closed:
            gt = ">="
            lt = "<="
        else:
            gt = ">"
            lt = "<"
            
        # Select slots which are partially occupied at that time
        sql = """select nod_id, sl_id, sl_capacity - sum(all_amount) as available  
        from v_allocslot 
        where ? %s ALL_SCHEDSTART AND ? < ALL_SCHEDEND""" % (gt)

        if type != None:
            filter = "slt_id = %i" % type
        if slots != None:
            filter = "sl_id in (%s)" % slots.__str__().strip('[]') 
       
        sql += " AND %s" % filter
        
        sql += " group by sl_id" 
        
        if amount != None:
            sql += " having available >= %f" % amount

        # And add slots which are completely free
        sql += " union select nod_id as nod_id, sl_id as sl_id, sl_capacity as available from v_allocslot va"
        sql += " where %s" % filter
        sql += """and not exists 
        (select * from tb_alloc a 
         where a.sl_id=va.sl_id and  
         ? %s ALL_SCHEDSTART AND ? < ALL_SCHEDEND)""" % (gt)

        cur = self.getConn().cursor()
        cur.execute(sql, (time, time, time, time))
        
        return cur          

    def findChangePoints(self, start, end, slot, closed=True):
        if closed:
            gt = ">="
            lt = "<="
        else:
            gt = ">"
            lt = "<"
        
        sql = """select distinct all_schedstart as time from tb_alloc 
        where sl_id=? and all_schedstart %s ? and all_schedstart %s ?
        union select distinct all_schedend as time from tb_alloc 
        where sl_id=? and all_schedend %s ? and all_schedend %s ?"""  % (gt,lt,gt,lt)

        cur = self.getConn().cursor()
        cur.execute(sql, (slot, start, end, slot, start, end))
        
        return cur
        
        
    def getReservationsWithStartingAllocationsInInterval(self, time, td, **kwargs):
        distinctfields=("RES_ID","RES_NAME","RES_STATUS")
        return self.getAllocationsInInterval(time,td=td,eventfield="all_schedstart", distinct=distinctfields, **kwargs)

    def getResPartsWithStartingAllocationsInInterval(self, time, td, **kwargs):
        distinctfields=("RSP_ID","RSP_NAME","RSP_STATUS")
        return self.getAllocationsInInterval(time,td=td,eventfield="all_schedstart", distinct=distinctfields, **kwargs)

    def getReservationsWithEndingAllocationsInInterval(self, time, td, **kwargs):
        distinctfields=("RES_ID","RES_NAME","RES_STATUS")
        return self.getAllocationsInInterval(time,td=td,eventfield="all_schedend", distinct=distinctfields, **kwargs)

    def getResPartsWithEndingAllocationsInInterval(self, time, td, **kwargs):
        distinctfields=("RSP_ID","RSP_NAME","RSP_STATUS")
        return self.getAllocationsInInterval(time,td=td,eventfield="all_schedend", distinct=distinctfields, **kwargs)

    def getFutureAllocationsInSlot(self, time, sl_id, **kwargs):
        return self.getAllocationsInInterval(time, td=None, eventfield="all_schedstart",sl_id=sl_id,**kwargs)

    def getCurrentAllocationsInSlot(self, time, sl_id, **kwargs):
        return self.getAllocationsInInterval(time, td=None, eventfield="all_schedend",sl_id=sl_id,**kwargs)

    
    def updateReservationStatus(self, res_id, status):
        sql = "UPDATE TB_RESERVATION SET RES_STATUS = ? WHERE RES_ID = ?"
        cur = self.getConn().cursor()
        cur.execute(sql, (status,res_id))

    
    def updateReservationPartStatus(self, respart_id, status):
        sql = "UPDATE TB_RESPART SET RSP_STATUS = ? WHERE RSP_ID = ?"
        cur = self.getConn().cursor()
        cur.execute(sql, (status,respart_id))

    def updateAllocationStatusInInterval(self, status, respart=None, start=None, end=None):
        sql = "UPDATE TB_ALLOC SET ALL_STATUS = ? WHERE "
        if respart != None:
            sql += " RSP_ID=%i" % respart
            
        if start != None:
            sql += " AND all_schedstart >= ? AND all_schedstart < ?"
            interval = start
        elif end != None:
            sql += " AND all_schedend >= ? AND all_schedend < ?"
            interval = end
        
        cur = self.getConn().cursor()
        cur.execute(sql, (status,) + interval)

    def updateAllocation(self, sl_id, rsp_id, all_schedstart, newstart=None, end=None):
        print "Updating allocation %i,%i beginning at %s with start time %s and end time %s" % (sl_id, rsp_id, all_schedstart, newstart, end)
        sql = """UPDATE tb_alloc 
        SET all_schedstart=?, all_schedend=?
        WHERE sl_id = ? AND rsp_id = ? AND all_schedstart = ?"""
        cur = self.getConn().cursor()
        cur.execute(sql, (newstart,end,sl_id,rsp_id,all_schedstart))

    def addReservation(self, name):
        sql = "INSERT INTO tb_reservation(res_name,res_status) values (?,0)"
        cur = self.getConn().cursor()
        cur.execute(sql, (name,))
        res_id=cur.lastrowid
        return res_id
    
    def addReservationPart(self, res_id, name, type):
        sql = "INSERT INTO tb_respart(rsp_name,res_id,rspt_id,rsp_status) values (?,?,?,0)"
        cur = self.getConn().cursor()
        cur.execute(sql, (name,res_id,type))
        rsp_id=cur.lastrowid
        return rsp_id
    
    def addSlot(self, rsp_id, sl_id, startTime, endTime, amount, moveable=False, deadline=None, duration=None):
        print "Reserving %f in slot %i from %s to %s" % (amount, sl_id, startTime, endTime)
        sql = "INSERT INTO tb_alloc(rsp_id,sl_id,all_schedstart,all_schedend,all_amount,all_moveable,all_deadline,all_duration,all_status) values (?,?,?,?,?,?,?,?,0)"
        cur = self.getConn().cursor()
        cur.execute(sql, (rsp_id, sl_id, startTime, endTime, amount, moveable, deadline, duration))            

    def isReservationDone(self, res_id):
        sql = "SELECT COUNT(*) FROM V_ALLOCATION WHERE res_id=? AND all_status in (0,1)" # Hardcoding bad!
        cur = self.getConn().cursor()
        cur.execute(sql, (res_id,))
        
        count = cur.fetchone()[0]

        if count == 0:
            return True
        else:
            return False

    def commit(self):
        self.getConn().commit()

    def rollback(self):
        self.getConn().rollback()
    
class SQLiteReservationDB(ReservationDB):
    def __init__(self, dbfile):
        self.conn = sqlite.connect(dbfile, detect_types=sqlite.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite.Row
        
    def getConn(self):
        return self.conn