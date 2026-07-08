package com.jadsstudio.jadslink.data.remote

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Part
import retrofit2.http.Path

/**
 * Interfaz Retrofit para la API de operador de JADSLink.
 *
 * Todos los endpoints (salvo login/signup/exchange) requieren el header
 * Authorization: Bearer <token>, que añade automáticamente AuthInterceptor.
 *
 * Se usan funciones `suspend` (corrutinas). Si prefieres Result<T> o Response<T>
 * envuélvelo en tu repositorio.
 */
interface JadsLinkApi {

    // ─────────────────────── AUTH ───────────────────────
    @POST("api/auth/login")
    suspend fun login(@Body body: LoginPayload): AuthResult

    @POST("api/signup")
    suspend fun signup(@Body body: SignupPayload): AuthResult

    @GET("api/auth/me")
    suspend fun me(): Me

    @PUT("api/auth/password")
    suspend fun changePassword(@Body body: ChangePasswordPayload): ChangePasswordResult

    @POST("api/auth/logout")
    suspend fun logout(): SimpleOk

    // ─────────────────────── CUENTA / PLAN ───────────────────────
    @GET("api/plans")
    suspend fun plans(): List<Plan>

    @GET("api/accounts/{accountId}")
    suspend fun account(@Path("accountId") accountId: String): Account

    @GET("api/accounts/{accountId}/users")
    suspend fun accountUsers(@Path("accountId") accountId: String): List<AccountUser>

    @GET("api/accounts/{accountId}/tickets/quota")
    suspend fun quota(@Path("accountId") accountId: String): Quota

    // ─────────────────────── PAGOS ───────────────────────
    @GET("api/accounts/{accountId}/payments")
    suspend fun payments(@Path("accountId") accountId: String): List<Payment>

    /**
     * Reportar pago de suscripción (multipart). Construye las partes con
     * [PaymentParts] o manualmente. `proof` es opcional.
     */
    @Multipart
    @POST("api/accounts/{accountId}/payments")
    suspend fun reportPayment(
        @Path("accountId") accountId: String,
        @Part("amount_usd") amountUsd: RequestBody,
        @Part("method") method: RequestBody,
        @Part("reference") reference: RequestBody,
        @Part("note") note: RequestBody,
        @Part proof: MultipartBody.Part? = null,
    ): Payment

    // ─────────────────────── DASHBOARD ───────────────────────
    @GET("api/devices/overview")
    suspend fun overview(): Overview

    // ─────────────────────── GATEWAYS ───────────────────────
    @GET("api/devices")
    suspend fun devices(): List<Device>

    @POST("api/devices/register")
    suspend fun registerDevice(@Body body: DeviceRegister): DeviceCredentials

    @POST("api/devices/activate")
    suspend fun activateDevice(@Body body: DeviceActivate): DeviceCredentials

    @GET("api/devices/{deviceId}")
    suspend fun device(@Path("deviceId") deviceId: String): Device

    @PATCH("api/devices/{deviceId}")
    suspend fun updateDevice(
        @Path("deviceId") deviceId: String,
        @Body body: DeviceUpdate,
    ): Device

    @DELETE("api/devices/{deviceId}")
    suspend fun deleteDevice(@Path("deviceId") deviceId: String): SimpleOk

    @PUT("api/devices/{deviceId}/config")
    suspend fun updateConfig(
        @Path("deviceId") deviceId: String,
        @Body body: ConfigUpdate,
    ): SimpleOk

    @GET("api/devices/{deviceId}/onboarding")
    suspend fun onboarding(@Path("deviceId") deviceId: String): Map<String, Any?>

    @GET("api/devices/{deviceId}/clients")
    suspend fun clients(@Path("deviceId") deviceId: String): List<ConnectedClient>

    @POST("api/devices/{deviceId}/kick/{mac}")
    suspend fun kickClient(
        @Path("deviceId") deviceId: String,
        @Path("mac") mac: String,
    ): SimpleOk

    @GET("api/devices/{deviceId}/usage-summary")
    suspend fun usageSummary(@Path("deviceId") deviceId: String): Map<String, Any?>

    @GET("api/devices/{deviceId}/reports")
    suspend fun reports(@Path("deviceId") deviceId: String): List<Report>

    @GET("api/devices/{deviceId}/logs")
    suspend fun logs(@Path("deviceId") deviceId: String): Map<String, Any?>

    @POST("api/devices/{deviceId}/reboot")
    suspend fun reboot(@Path("deviceId") deviceId: String): SimpleOk

    @POST("api/devices/{deviceId}/ssid")
    suspend fun setSsid(
        @Path("deviceId") deviceId: String,
        @Body body: SsidUpdate,
    ): SimpleOk

    // ─────────────────────── CÓDIGOS ───────────────────────
    @GET("api/devices/{deviceId}/codes")
    suspend fun codes(@Path("deviceId") deviceId: String): List<Code>

    @POST("api/devices/{deviceId}/codes")
    suspend fun generateCodes(
        @Path("deviceId") deviceId: String,
        @Body body: CodeCreate,
    ): CodeCreateResult

    @DELETE("api/devices/{deviceId}/codes/{codeId}")
    suspend fun deleteCode(
        @Path("deviceId") deviceId: String,
        @Path("codeId") codeId: Int,
    ): SimpleOk

    // ─────────────────────── TIENDA / VENTAS ───────────────────────
    @GET("api/products")
    suspend fun products(): List<Product>

    @POST("api/products")
    suspend fun createProduct(@Body body: ProductCreate): Product

    @PATCH("api/products/{productId}")
    suspend fun updateProduct(
        @Path("productId") productId: Int,
        @Body body: ProductUpdate,
    ): Product

    @DELETE("api/products/{productId}")
    suspend fun deleteProduct(@Path("productId") productId: Int): SimpleOk

    @GET("api/orders")
    suspend fun orders(): List<Order>

    @POST("api/orders/{orderId}/approve")
    suspend fun approveOrder(@Path("orderId") orderId: Int): Order

    @POST("api/orders/{orderId}/reject")
    suspend fun rejectOrder(
        @Path("orderId") orderId: Int,
        @Body body: RejectPayload,
    ): Order

    // ─────────────────────── EXTRAS ───────────────────────
    @GET("api/exchange/current")
    suspend fun exchangeRate(): ExchangeRate

    @GET("api/groups")
    suspend fun groups(): List<Group>

    @POST("api/groups")
    suspend fun createGroup(@Body body: GroupCreate): Group
}
