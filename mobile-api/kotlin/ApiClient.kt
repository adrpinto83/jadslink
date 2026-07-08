package com.jadsstudio.jadslink.data.remote

import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.io.File

/**
 * Almacén del token. Reemplaza por DataStore/EncryptedSharedPreferences en la app;
 * aquí se deja una implementación en memoria para el ejemplo.
 */
interface TokenStore {
    fun get(): String?
    fun set(token: String?)
}

class InMemoryTokenStore : TokenStore {
    @Volatile private var token: String? = null
    override fun get() = token
    override fun set(token: String?) { this.token = token }
}

/**
 * Añade Authorization: Bearer <token> cuando hay sesión.
 */
class AuthInterceptor(private val tokens: TokenStore) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokens.get()
        val request: Request = if (token.isNullOrBlank()) {
            chain.request()
        } else {
            chain.request().newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        }
        return chain.proceed(request)
    }
}

/**
 * Detecta 401 (sesión expirada / contraseña cambiada). Llama a [onUnauthorized]
 * para que la app limpie el token y redirija al login.
 */
class UnauthorizedInterceptor(private val onUnauthorized: () -> Unit) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val response = chain.proceed(chain.request())
        if (response.code == 401) onUnauthorized()
        return response
    }
}

object ApiClient {

    /** En producción: https://link.jadsstudio.com/ (¡con la barra final!). */
    const val BASE_URL = "https://link.jadsstudio.com/"

    val tokenStore: TokenStore = InMemoryTokenStore()

    private val moshi: Moshi = Moshi.Builder()
        .add(KotlinJsonAdapterFactory())
        .build()

    fun create(
        baseUrl: String = BASE_URL,
        onUnauthorized: () -> Unit = {},
        debug: Boolean = false,
    ): JadsLinkApi {
        val builder = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(tokenStore))
            .addInterceptor(UnauthorizedInterceptor(onUnauthorized))

        if (debug) {
            builder.addInterceptor(
                HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BODY }
            )
        }

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(builder.build())
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
            .create(JadsLinkApi::class.java)
    }
}

/**
 * Helpers para armar las partes multipart del reporte de pago.
 *
 * Ejemplo:
 * ```
 * val parts = PaymentParts.build(
 *     amountUsd = 29.0, method = "pago_movil", reference = "0102-1234",
 *     note = "Pago mensual", proof = File(...) // opcional
 * )
 * api.reportPayment(accountId, parts.amountUsd, parts.method,
 *                   parts.reference, parts.note, parts.proof)
 * ```
 */
object PaymentParts {
    private val TEXT = "text/plain".toMediaType()

    data class Parts(
        val amountUsd: RequestBody,
        val method: RequestBody,
        val reference: RequestBody,
        val note: RequestBody,
        val proof: MultipartBody.Part?,
    )

    fun build(
        amountUsd: Double,
        method: String,
        reference: String = "",
        note: String = "",
        proof: File? = null,
    ): Parts {
        val proofPart = proof?.let {
            val mime = when (it.extension.lowercase()) {
                "png" -> "image/png"
                "webp" -> "image/webp"
                "pdf" -> "application/pdf"
                else -> "image/jpeg"
            }
            MultipartBody.Part.createFormData(
                "proof", it.name, it.asRequestBody(mime.toMediaType())
            )
        }
        return Parts(
            amountUsd = RequestBody.create(TEXT, amountUsd.toString()),
            method = RequestBody.create(TEXT, method),
            reference = RequestBody.create(TEXT, reference),
            note = RequestBody.create(TEXT, note),
            proof = proofPart,
        )
    }
}
