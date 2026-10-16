package demo

import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service

@Service
class MainKotlinService {
  @Value("\${my.property}")                  // TC-01K
  lateinit var myProperty: String

  @Value("\${test.only.property}")           // NC-01K
  lateinit var testOnly: String
}
