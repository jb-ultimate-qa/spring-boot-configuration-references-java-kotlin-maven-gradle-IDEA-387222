package demo

import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Value
import org.springframework.boot.test.context.SpringBootTest

@SpringBootTest
class MainKotlinServiceTest {
  @Value("\${test.only.property}")           // TC-05K
  lateinit var testOnly: String

  @Test
  fun contextLoads() {
  }
}
