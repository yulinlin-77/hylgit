@app.route('/api/bookings/<booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    # 1. 接收前端传来的数据
    user_id = request.json.get('user_id')
    cancel_reason = request.json.get('cancel_reason')

    try:
        # 开启数据库事务 (Transaction) -> 报告拿分点：保证数据一致性
        db.begin_transaction()

        # 2. 查出这条订单和对应的时间槽
        booking = db.query("SELECT * FROM Bookings WHERE booking_id = ?", booking_id)
        time_slot = db.query("SELECT * FROM Time_Slots WHERE slot_id = ?", booking.slot_id)

        # 3. 拦截器 1：越权操作检查 (Security/RBAC)
        if booking.customer_id != user_id:
            return {"error": "无权取消他人的订单"}, HTTP_403_FORBIDDEN

        # 4. 拦截器 2：状态机规则检查 (State Machine Rules)
        if booking.status in ['Completed', 'Cancelled']:
            return {"error": f"当前状态为 {booking.status}，不可取消"}, HTTP_400_BAD_REQUEST

        # 5. 拦截器 3：24小时业务规则检查 (Business Rule: Boundary Value)
        current_time = get_current_time()
        time_difference = time_slot.start_time - current_time
        
        if time_difference < 24_hours:
            return {"error": "距离预约开始不足24小时，无法取消"}, HTTP_400_BAD_REQUEST

        # ================= 核心状态更新 =================
        # 6. 更新 Bookings 表：状态改为 Cancelled，写入原因
        db.execute("""
            UPDATE Bookings 
            SET status = 'Cancelled', cancel_reason = ? 
            WHERE booking_id = ?
        """, (cancel_reason, booking_id))

        # 7. 更新 Time_Slots 表：释放时间槽，让别人可以重新预订
        db.execute("""
            UPDATE Time_Slots 
            SET is_available = TRUE 
            WHERE slot_id = ?
        """, (booking.slot_id))

        # 提交数据库事务
        db.commit_transaction()

        # 8. 返回符合规范的成功状态码
        return {"message": "取消成功，时间槽已释放"}, HTTP_200_OK

    except Exception as e:
        # 发生任何错误，回滚数据，防止数据库损坏
        db.rollback_transaction()
        return {"error": "服务器内部错误"}, HTTP_500_INTERNAL_SERVER_ERROR
        